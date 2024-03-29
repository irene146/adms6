#   Copyright (C) 2004 CCLRC & NERC( Natural Environment Research Council ).
#   This software may be distributed under the terms of the
#   Q Public License, version 1.0 or later. http://ndg.nerc.ac.uk/public_docs/QPublic_license.txt

"""
na_content_collector.py
=======================

Holds the class NAContentCollector that converts a set of Xarray DataArrays and global attributes to 
a NASA Ames dictionary.

"""

# Imports from python standard library
import sys
import time
import re
import logging

# Third-party imports
import numpy as np
import xarray as xr
import cftime

# Import from nappy package
import nappy.utils
import nappy.utils.common_utils
import nappy.na_file.na_core

from . import xarray_utils

config_dict = nappy.utils.getConfigDict()
nc_to_na_map = config_dict["nc_to_na_map"]
header_partitions = config_dict["header_partitions"]
hp = header_partitions

version = nappy.utils.getVersion()
DEBUG = nappy.utils.getDebug() 

log = logging.getLogger(__name__)


class NAContentCollector(nappy.na_file.na_core.NACore):
    """
    Class to build a NASA Ames File object from a set of 
    Xarray DataArrays and global attributes (optional).
    """
    
    def __init__(self, variables, global_attributes=None, requested_ffi=None):
        """
        Sets up instance variables and calls appropriate methods to
        generate sections of NASA Ames file object.

        Input arguments are:
          * variables - list/tuple of actual Xarray variables
          * global_attributes - list of user-defined global (key,value) attributes to include.

        Typical usage:
        >>> x = NAContentCollector(["temp", "precip"])
        >>> x.collectNAContent()
        >>> if x.found_na:
        ...     print(x.na_dict, x.var_ids, x.unused_vars)
        """
        global_attributes = global_attributes or []

        self.output_message = []
        self.na_dict = {}
        self.vars = variables

        # Note that self.var_ids will be a list containing:
        #    [ordered_vars, auxiliary_vars, rank_zero_vars]
        self.var_ids = None
        self.globals = dict(global_attributes)
        self.requested_ffi = requested_ffi

        self.rank_zero_vars = []
        self.rank_zero_var_ids = []

        # Create a flag to check if anything found
        self.found_na = False

    def collectNAContent(self):
        """
        Collect NASA Ames content. Save the contents to the following instance
        attributes:
         * self.na_dict
         * self.var_ids
         * self.unused_vars
        """
        log.debug("Call to collectNAContent():\n")

        for v in self.vars: 
            log.debug(f"\t{v.name}, {v.shape}, {v.dims}")
 
        (self.ordered_vars, aux_vars) = self._analyseVariables()
     
        if self.ordered_vars == []:
            log.warn("No NASA Ames content created.")
            self.unused_vars = []
        else:
            self.var_ids = [[var.name for var in self.ordered_vars],
                            [var.name for var in aux_vars], 
                            self.rank_zero_var_ids]

            self.na_dict["NLHEAD"] = -999
            self._defineNAVars(self.ordered_vars)
            self._defineNAAuxVars(aux_vars)
            self._defineNAGlobals()
            self._defineNAComments()
            self._defineGeneralHeader()
            self.found_na = True

    def _analyseVariables(self):
        """
        Method to examine the content of Xarray variables to return
        a tuple of two lists containing variables and auxiliary variables
        for the NASA Ames file object.
        Variables not compatible with the first file are put in self.unused_vars
        """
        self.unused_vars = []
        ffis_limited = False

        highest_rank = -1
        best_var = None
        count = 0

        # Need to get highest ranked variable (most dimensions) so that we can work out FFI
        for var in self.vars:
            msg = f"Analysing: {var.name}"
            self.output_message.append(msg)
            count = count + 1

            # get rank
            rank = len(var.shape)

            # Deal with singleton variables
            if rank == 0: 
                self.rank_zero_vars.append(var)
                self.rank_zero_var_ids.append(var.name)
                continue

            # Update highest if highest found or if equals highest with bigger size
            try:
                var.size = var.size()
                best_var.size = best_var.size()
            except:
                pass

            if rank > highest_rank or (rank == highest_rank and var.size > best_var.size):
                highest_rank = rank
                best_var = var
                best_var_index = count - 1

        # If all are zero ranked variables or no vars identified/found then we cannot write any to NASA Ames and return ([], [])
        if len(self.rank_zero_vars) == len(self.vars) or best_var is None: 
            return ([], [])

        # Now start to sort the variables into main and auxiliary 
        vars_for_na = [best_var]
        aux_vars_for_na = []
        shape = best_var.shape
        number_of_dims = len(shape)
        self.na_dict["NIV"] = number_of_dims

        # If 2D then do a quick test to see if 2310 is feasible (i.e. uniformly spaced 2nd axis)
        if number_of_dims == 2:

            ffis_limited = [2010, 2110]
            axis = xarray_utils.get_coord_by_index(best_var, 1)

            if xarray_utils.isUniformlySpaced(axis):
                ffis_limited.append(2310)

        # Get the axes for the main variable being used
        best_var_axes = xarray_utils.getAxisList(best_var)
        
        # Get other variables into a list and analyse them
        rest_of_the_vars = self.vars[:best_var_index] + self.vars[(best_var_index + 1):]

        for var in rest_of_the_vars:

            if var.name in self.rank_zero_var_ids: continue

            # What to do with variables that have different number of dimensions or different shape
            if len(var.shape) != number_of_dims or var.shape != shape: 
                # Could it be an auxiliary variable?
                if len(var.shape) != 1: 
                    self.unused_vars.append(var)
                    continue

                first_axis = xarray_utils.get_coord_by_index(var, 0)
                # Check if axis is identical to first axis of main best variable, if so, can be auxiliary var
                if not xarray_utils.areAxesIdentical(best_var_axes[0], first_axis):

                    # If not identical, then it might still qualify as an auxiliary every n time points - valid for 1020
                    if len(var.shape) == 1:
                        nvpm = xarray_utils.isAxisRegularlySpacedSubsetOf(first_axis, best_var_axes[0])

                        # NVPM is the number of implied values which is equal to (len(ax2)/len(ax1))
                        if nvpm:
                            ffis_limited = [1020]
                            self.na_dict["NVPM"] = nvpm
                        else: # if returned False, i.e. not regular subset axis
                            self.unused_vars.append(var)

                    else:
                        self.unused_vars.append(var)
                        continue

                else:
                    # This could be used as a standard auxiliary variable
                    if ffis_limited in ([1020],):
                        # Already fixed on 1020 and cannot collect incompatible FFI vars so do not use
                        self.unused_vars.append(var)
                    else:
                        aux_vars_for_na.append(var) 

            else:
                this_var_axes = xarray_utils.getAxisList(var)

                # Loop through dimensions
                for i in range(number_of_dims):            

                    if not xarray_utils.areAxesIdentical(best_var_axes[i], this_var_axes[i]):
                        self.unused_vars.append(var)
                        break
                else:
                    # OK, I think the current variable is compatible to write with the best variable along with a NASA Ames file 
                    vars_for_na.append(var)

        # Send vars_for_na AND aux_vars_for_na to a method to check if they have previously been mapped 
        # from NASA Ames. In which case we'll write them back in the order they were initially read from the input file.
        (vars_for_na, aux_vars_for_na) = \
            self._reorderVarsIfPreviouslyNA(vars_for_na, aux_vars_for_na)

        # Get the FFI
        self.na_dict["FFI"] = \
            self._decideFileFormatIndex(number_of_dims, aux_vars_for_na, ffis_limited)

        return vars_for_na, aux_vars_for_na

    def _reorderVarsIfPreviouslyNA(self, vars_for_na, aux_vars_for_na):
        """
        Re-order if they previously came from NASA Ames files (i.e. including the 
        attribute 'nasa_ames_var_number'). Return re-ordered or unchanged pair of
        (vars_for_na, aux_vars_for_na).
        """
        # First do the main variables
        ordered_vars = [None] * 1000 # Make a long list to put vars in 

        # Create a list of other variables to collect up any that are not labelled as nasa ames variables
        other_vars = []
        for var in vars_for_na:
            if hasattr(var, "nasa_ames_var_number"):
                ordered_vars[var.nasa_ames_var_number] = var
            else:
                other_vars.append(var)

        # Remake vars_for_na now in new order and clean out any that are "None"
        vars_for_na = []
        for var in ordered_vars:
            if var is not None: 
                vars_for_na.append(var)

        vars_for_na = vars_for_na + other_vars

        # Now re-order the Auxiliary variables if they previously came from NASA 
        ordered_aux_vars = [None] * 1000
        other_aux_vars = []

        for var in aux_vars_for_na:
            if hasattr(var, "nasa_ames_aux_var_number"):
                ordered_aux_vars[var.nasa_ames_aux_var_number] = var
            else:
                other_aux_vars.append(var)

        # Remake aux_vars_for_na now in order
        aux_vars_for_na = []
        for var in ordered_aux_vars:
            if type(var) != type(None): 
                aux_vars_for_na.append(var)

        aux_vars_for_na = aux_vars_for_na + other_aux_vars
        return (vars_for_na, aux_vars_for_na)

    def _decideFileFormatIndex(self, number_of_dims, aux_vars_for_na, ffis_limited=False):
        """
        Based on the number of dimensions and the NASA Ames dictionary return
        the File Format Index. 
        If there is a choice then make the most sensible selection.
        If the user has specified a 'requested_ffi' then try and deliver
        that. Raise an error if not possible.
        """
        # If ffis_limited is set then must use one of those
        if self.requested_ffi and ffis_limited:

            if self.requested_ffi not in ffis_limited:
                raise Exception(f"Cannot write this data to FFI '{self.requested_ffi}', can only write to: {ffis_limited}.")
            else:
                return self.requested_ffi

        # Base the sub-selection on number of dimensions
        if number_of_dims > 4:
            raise Exception("Cannot write variables defined against greater than 4 axes in NASA Ames format.")
        elif number_of_dims > 2: 
            ffi = 10 + (number_of_dims * 1000)
        elif number_of_dims == 2:
            if self.requested_ffi in (2010, 2110, 2310):
                ffi = self.requested_ffi 
            else:
                ffi = 2010
        else:
            if len(aux_vars_for_na) > 0 or ("NAUXV" in self.na_dict and self.na_dict["NAUXV"] > 0):
                ffi = 1010
            else:
                ffi = 1001

        if self.requested_ffi and ffi != self.requested_ffi:
            raise Exception("Cannot write this data to FFI '" + str(self.requested_ffi) + "', can only write to: " + str(ffi) + ".")
        return ffi

    def _resolve_float(self, item):
        """
        Gets a float from a number of different types of object.
        """
        if not type(item) in (float, int, str, np.number) and not np.isscalar(item):
            if isinstance(item, np.ndarray) and item.shape == ():
                item = float(item)
            else:
                item = item[0]

        return item

    def _defineNAVars(self, vars):
        """
        Method to define NASA Ames file object variables and their
        associated metadata.
        """
        self.na_dict["NV"] = len(vars)
        self.na_dict["VNAME"] = []
        self.na_dict["VMISS"] = []
        self.na_dict["VSCAL"] = []
        self.na_dict["V"] = []

        for var in vars:
            name = xarray_utils.getBestName(var)
            self.na_dict["VNAME"].append(name)
            miss = xarray_utils.getMissingValue(var)
            miss = self._resolve_float(miss)

            self.na_dict["VMISS"].append(miss)
            self.na_dict["VSCAL"].append(1)

            # Populate the variable list with the array
            # Make sure missing values are converted to real values using the required missing value
            self.na_dict["V"].append(xarray_utils.getArrayAsList(var, missing_value=miss, handle_datetimes=True))

            # Create independent variable info
            if not "X" in self.na_dict:

                # Set up lists ready to populate with values
                self.na_dict["NXDEF"] = []
                self.na_dict["NX"] = []

                self.ax0 = xarray_utils.get_coord_by_index(var, 0)

                self.na_dict["X"] = [xarray_utils.getArrayAsList(self.ax0)]
                self.na_dict["XNAME"] = [xarray_utils.getBestName(self.ax0)]

                if len(self.ax0) == 1:
                    self.na_dict["DX"] = [0]
                else:
                    # Set default increment as gap between first two
                    incr = xarray_utils.get_interval(self.ax0, 0, 1)

                    self.na_dict["DX"] = [incr]
                    # Now overwrite it as zero if non-uniform interval in axis

                    for i in range(1, len(self.ax0)):
                        if xarray_utils.get_interval(self.ax0, i-1, i) != incr:
                            self.na_dict["DX"] = [0]
                            break

                # If 1D only then "X" should only be a list and not list of lists
                if self.na_dict["FFI"] in (1001, 1010, 1020):
                    self.na_dict["X"] = self.na_dict["X"][0]

                # If FFI is 1020 need to reduce axis down to reduced values as most are implied
                if self.na_dict["FFI"] == 1020: 
                    vals = self.na_dict["X"]
                    self.na_dict["X"] = vals[0:len(vals):self.na_dict["NVPM"]] 

                # Now add the rest of the axes to the self.na_dict objects 
                for axis in xarray_utils.getAxisList(var)[1:]:
                    self._appendAxisDefinition(axis)

                # If FFI is 2110 then need to modify the "NX" and "X" lists to cope with odd shape
                # Also need to add NX to auxiliary variables
                if self.na_dict["FFI"] == 2110:
                    new_x = []
                    new_nx = []
                    ax2_values = xarray_utils.get_coord_by_index(var, 1).data.tolist()

                    for i in self.ax0[:]:
                        new_x.append([i, ax2_values])
                        new_nx.append(len(ax2_values))

                    # Re-assign to new lists
                    self.na_dict["NX"] = new_nx
                    self.na_dict["X"] = new_x                    

                    # Now auxiliary variable info here with independent var info
                    # First aux var is NX
                    self.na_dict["A"] = [self.na_dict["NX"][:]]
                    ind_var_name = self.na_dict["XNAME"][0]
                    self.na_dict["ANAME"] = ["Number of '%s' values recorded in subsequent data records" % ind_var_name]
                    self.na_dict["AMISS"] = [-9999.999]
                    self.na_dict["ASCAL"] = [1.0]

                # If FFI is 2310 then need to modify na_dict items for that
                elif self.na_dict["FFI"] == 2310:
                    new_x = []
                    new_nx = []
                    new_dx = []
                    ax2_values = xarray_utils.get_coord_by_index(var, 1).data.tolist()
                    incr = xarray_utils.get_interval(ax2_values, 0, 1)

                    for i in self.ax0[:]:
                        new_x.append([i, ax2_values])
                        new_nx.append(len(ax2_values))
                        new_dx.append(incr)

                    # Re-assign to new lists
                    self.na_dict["NX"] = new_nx
                    self.na_dict["X"] = new_x
                    self.na_dict["DX"] = new_dx

                    # Now auxiliary variable info here with independent var info
                    # First three aux vars are NX, X0 and DX
                    self.na_dict["A"] = []
                    self.na_dict["A"].append(self.na_dict["NX"][:])
                    self.na_dict["A"].append([i[1][0] for i in self.na_dict["X"]])
                    self.na_dict["A"].append(self.na_dict["DX"][:])

                    ind_var_name = self.na_dict["XNAME"][0]
                    self.na_dict["ANAME"] = ["Number of '%s' values recorded in subsequent data records" % ind_var_name,
                                             "'%s' value for first data point" % ind_var_name,
                                             "'%s' increment" % ind_var_name]
                    self.na_dict["AMISS"] = [-9999.999, -9999.999, -9999.999]
                    self.na_dict["ASCAL"] = [1.0, 1.0, 1.0]
 

    def _defineNAAuxVars(self, aux_vars):
        """
        Method to define NASA Ames file object auxiliary variables and their
        associated metadata. Note that "A" may already have content if
        independent variable items (relating to "X") are defined as aux vars.
        """
        # Initialise aux var itesms as empty lists unless already defined when
        # setting up independent variables
        for item in ("ANAME", "AMISS", "ASCAL", "A"):
            if not item in self.na_dict:
                self.na_dict[item] = [] 

        for var in aux_vars:
            name = xarray_utils.getBestName(var)
            self.na_dict["ANAME"].append(name)
            miss = xarray_utils.getMissingValue(var)
            miss = self._resolve_float(miss)

            self.na_dict["AMISS"].append(miss)
            self.na_dict["ASCAL"].append(1)
            # Populate the variable list with the array
            self.na_dict["A"].append(xarray_utils.getArrayAsList(var, missing_value=miss))

        self.na_dict["NAUXV"] = len(self.na_dict["A"])

    def _appendAxisDefinition(self, axis):
        """
        Method to create the appropriate NASA Ames file object 
        items associated with an axis (independent variable in 
        NASA Ames). It appends to the various self.na_dict containers.
        """
        length = len(axis)

        self.na_dict["NX"].append(length)
        self.na_dict["XNAME"].append(xarray_utils.getBestName(axis))

        # If only one item in axis values
        if length < 2:
            self.na_dict["DX"].append(0)
            self.na_dict["NXDEF"].append(length)
            self.na_dict["X"].append(axis.data.tolist())        
            return

        incr = xarray_utils.get_interval(axis, 0, 1)

        for i in range(1, length):
            if (axis[i] - axis[i - 1]) != incr:
                self.na_dict["DX"].append(0)
                self.na_dict["NXDEF"].append(length)
                self.na_dict["X"].append(axis.data.tolist())
                break

        else: # If did not break out of the loop
            max_length = length
            if length > 3: 
                max_length = 3

            self.na_dict["DX"].append(incr)
            self.na_dict["NXDEF"].append(max_length)
            self.na_dict["X"].append(axis[:max_length])

    def _defineNAGlobals(self):
        """
        Maps Xarray (NetCDF) global attributes into NASA Ames Header fields.
        """
        # Check if we should add to it with locally set rules
        local_attributes = nappy.utils.getLocalAttributesConfigDict()
        local_nc_atts = local_attributes["nc_attributes"]
        local_nc_to_na_map = nc_to_na_map.copy()

        for att, value in local_nc_atts.items():
            if att not in local_nc_to_na_map:
                local_nc_to_na_map[key] = value

        self.extra_comments = [[], [], []]  # Normal comments, special comments, other comments

        for key, value in self.globals.items():
            if key != "first_valid_date_of_data" and \
                    type(value) not in (str, int, float):
                continue

            # Loop through keys of header/comment items to map
            if key in local_nc_to_na_map:
                if key == "history":
                    time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                    history = "History:  %s - Converted to NASA Ames format using nappy-%s.\n  %s" % \
                                                 (time_string, version, value)
                    history = history.split("\n") 
                    self.history = []

                    for h in history:
                        if h[:8] != "History:" and h[:1] != "  ": 
                            h = "  " + h
                        self.history.append(h) 
                    
                elif key == "institution":
                    # If fields came from NA then extract appropriate fields.
                    match = re.match(r"(.*)\s+\(ONAME from NASA Ames file\);\s+(.*)\s+\(ORG from NASA Ames file\)\.", 
                             value)
                    if match:
                        self.na_dict["ONAME"] = match.groups()[0]
                        self.na_dict["ORG"] = match.groups()[1]
                    else:
                        self.na_dict["ONAME"] = value
                        self.na_dict["ORG"] = value

                    # NOTE: should probably do the following search and replace on all string lines
                    self.na_dict["ONAME"] = self.na_dict["ONAME"].replace("\n", "  ")
                    self.na_dict["ORG"] = self.na_dict["ORG"].replace("\n", "  ")

                elif key == "comment":
                    # Need to work out if they are actually comments from NASA Ames in the first place
                    comment_lines = value.split("\n")
                    normal_comments = []
                    normal_comm_flag = None

                    special_comments = []
                    special_comm_flag = None

                    for line in comment_lines:

                        if line.find(hp["sc_start"]) > -1:
                            special_comm_flag = 1
                        elif line.find(hp["sc_end"]) > -1:
                            special_comm_flag = None
                        elif line.find(hp["nc_start"]) > -1:
                            normal_comm_flag = 1
                        elif line.find(hp["nc_end"]) > -1:
                            normal_comm_flag = None
                        elif special_comm_flag == 1:
                            special_comments.append(line)
                        elif normal_comm_flag == 1:
                            normal_comments.append(line)
                        elif line.find(hp["data_next"]) > -1:
                            pass
                        else:
                            normal_comments.append(line)

                    # Carefully merge any comments with other metadata found.
                    other_special_comments, other_normal_comments, other_extra_comments = \
                         [comms[:] for comms in self.extra_comments]

                    self.extra_comments = [
                        other_special_comments + special_comments, 
                        other_normal_comments + normal_comments, 
                        other_extra_comments
                    ]  

                elif key == "first_valid_date_of_data":
                    self.na_dict["DATE"] = value

                elif key in ("Conventions", "references"):
                    self.extra_comments[2].append(f"{key}:   {value}")
                else:
                    self.na_dict[local_nc_to_na_map[key]] = value
            else:
                self.extra_comments[2].append(f"{key}:   {value}")

    def _defineNAComments(self, normal_comments=None, special_comments=None):
        """
        Defines the Special and Normal comments sections in the NASA Ames file 
        object - including information gathered from the defineNAGlobals method.

        Starts with values provided for normal_comments and special_comments.
        """
        normal_comments = normal_comments or []
        special_comments = special_comments or []

        if hasattr(self, "NCOM"):  normal_comments = getattr(self, "NCOM") + normal_comments

        NCOM = []
        for ncom in normal_comments:
            NCOM.append(ncom)

        if len(NCOM) > 0:
            NCOM.append("")

        # Use third item in self.extra_comments and adds to NCOM
        if len(self.extra_comments[2]) > 0:
            for excom in self.extra_comments[2]:
                NCOM.append(excom)

        if len(self.extra_comments[1]) > 0:  
            NCOM.append(hp["addl_globals"])
            for excom in self.extra_comments[1]:
                NCOM.append(excom)

        if hasattr(self, "history"):
            for h in self.history:
                NCOM.append(h)
       
        # When NCOM has been defined then surround it in some extras 
        if len(NCOM) > 0:
            NCOM.insert(0, hp["nc_start"]) 
            NCOM.append("")
            NCOM.append(hp["nc_end"])
            NCOM.append(hp["data_next"])

        spec_comm_flag = None
        # Start with special_comments added in
        SCOM = []

        # Uses first item in self.extra_comments to start SCOM
        special_comments = special_comments + self.extra_comments[0]

        if len(special_comments) > 0: 
            SCOM = [hp["sc_start"]]
            spec_comm_flag = 1

        for scom in special_comments:
            SCOM.append(scom)

        used_var_atts = ("id",  "missing_value", "fill_value", 
                   "nasa_ames_var_number", "nasa_ames_aux_var_number")
        var_comm_flag = None

        # Create a string for the Special comments to hold rank-zero vars
        rank_zero_vars_string = []

        for var in self.rank_zero_vars:
            rank_zero_vars_string.append("  Variable %s: %s" % (var.name, xarray_utils.getBestName(var)))

            for att in var.attrs.keys():
                value = var.attrs[att]

                if isinstance(value, str) or np.isscalar(value):
                    rank_zero_vars_string.append("    %s = %s" % (att, var.attrs[att]))

        if len(rank_zero_vars_string) > 0:
            rank_zero_vars_string.insert(0, hp["sing_start"])
            rank_zero_vars_string.append(hp["sing_end"])

        # Loop through variables and add 
        for var in self.ordered_vars:
            varflag = "unused"
            var_name_written = False

            name = xarray_utils.getBestName(var)

            for scom, value in var.attrs.items():
                if hasattr(value, "__len__") and len(value) == 1:
                    value = value[0]

                if isinstance(value, str) or np.isscalar(value) and scom not in used_var_atts:
                    if varflag == "unused":
                        if var_comm_flag == None:
                            var_comm_flag = 1

                    if spec_comm_flag == None:
                        SCOM = [hp["sc_start"]] + rank_zero_vars_string
                        SCOM.append(hp["addl_vatts"])
                        SCOM.append(hp["ncatts_start"])
                        varflag = "using" 
                        spec_comm_flag = 1

                    if not var_name_written:
                        SCOM.append("  Variable %s: %s" % (var.name, name))
                        var_name_written = True

                    SCOM.append("    %s = %s" % (scom, value))

        if var_comm_flag == 1:  
            SCOM.append(hp["ncatts_end"])
        if spec_comm_flag == 1:
            SCOM.append(hp["sc_end"])

        # Strip out empty lines (or returns)
        NCOM_cleaned = []
        SCOM_cleaned = []

        for c in NCOM:
            if c.strip() not in ("", " ", "  "):
                # Replace new lines within one attribute with a newline and tab so easier to read
                lines = c.split("\n")
                for line in lines:
                    if line != lines[0]: 
                        line = "  " + line

                    NCOM_cleaned.append(line)

        for c in SCOM:
            if c.strip() not in ("", " ", "  "):
                # Replace new lines within one attribute with a newline and tab so easier to read
                lines = c.split("\n")

                for line in lines:
                    if line != lines[0]: 
                        line = "  " + line

                    SCOM_cleaned.append(line)

        self.na_dict["NCOM"] = NCOM_cleaned
        self.na_dict["NNCOML"] = len(self.na_dict["NCOM"])
        self.na_dict["SCOM"] = SCOM_cleaned
        self.na_dict["NSCOML"] = len(self.na_dict["SCOM"])

        return

    def _defineGeneralHeader(self, header_items=None):
        """
        Defines known header items and overwrites any with header_items 
        key/value pairs.
        """
        if header_items == None:
            header_items = {}

        warning_message = "Nappy Warning: Could not get the first date in the file. You will need to manually edit the output file."

        # Check if DATE field previously known in NASA Ames file
        time_now = [int(i) for i in time.strftime("%Y %m %d", time.localtime(time.time())).split()]

        if not "RDATE" in self.na_dict:
            self.na_dict["RDATE"] = time_now

        if xarray_utils.is_time(self.ax0):
            # Get first date in list
            try:
                units = self.ax0.encoding["units"]
                first_day = self.na_dict["X"][0]

                # Cope with "X" being a list or list of lists (for different FFIs)
                while hasattr(first_day, "__len__"):
                    first_day = first_day[0]

                self.na_dict["DATE"] = \
                    [getattr(cftime.num2date(first_day, units), attr) for attr in ('year', 'month', 'day')]                
            except Exception:
                msg = warning_message
                log.info(msg)
                self.output_message.append(msg)
                self.na_dict["DATE"] = [999] * 3 

        else: 
            if not "DATE" in self.na_dict:
                msg = warning_message
                log.info(msg)
                self.output_message.append(msg)
                self.na_dict["DATE"] = [999] * 3 
            else:
                pass # i.e. use existing DATE

        self.na_dict["IVOL"] = 1
        self.na_dict["NVOL"] = 1

        for key in header_items.keys():
            self.na_dict[key] = header_items[key]
