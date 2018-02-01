#!/usr/bin/env python

""" Convert MARBL_diagnostics file to tavg_contents
"""

#######################################

def _parse_args():
    """ Parse command line arguments
    """

    import argparse

    parser = argparse.ArgumentParser(description="Generate POP tavg contents from MARBL diagnostics",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Command line argument to point to MARBL diagnostics input file (required!)
    parser.add_argument('-i', '--ecosys_diagnostics_in', action='store', dest='ecosys_diagnostics_in',
                        required=True, help='File generated by MARBL_generate_diagnostics_file')

    # Command line argument to point to file containing list of MARBL diagnostics (required!)
    parser.add_argument('-d', '--MARBL_diagnostics_list_in', action='store', dest='MARBL_diagnostics_list_in',
                        required=True, help='File containing list of all MARBL diagnostics')

    # Command line argument to point to tavg_contents output file (required!)
    parser.add_argument('-t', '--tavg_contents_out', action='store', dest='tavg_contents_out',
                        required=True, help='Location of tavg_contents file to create (or append to)')

    # Command line argument to point to MARBL_diagnostics_operator output file (required!)
    parser.add_argument('-o', '--MARBL_diagnostics_operator_out', action='store', dest='MARBL_diagnostics_operator_out',
                        required=True, help='Location of MARBL_diagnostics_operator file to create')

    # Command line arguments for the different streams to use (low, medium, high)
    parser.add_argument('-l', '--low_frequency_stream', action='store', dest='low_frequency_stream',
                        type=int, default= 0, help='Stream to put low frequency output into (required if not lMARBL_tavg_all)')

    parser.add_argument('-m', '--medium_frequency_stream', action='store', dest='medium_frequency_stream',
                        type=int, default= 0, help='Stream to put medium frequency output into (required if not lMARBL_tavg_all)')

    parser.add_argument('-g', '--high_frequency_stream', action='store', dest='high_frequency_stream',
                        type=int, default= 0, help='Stream to put high frequency output into (required if not lMARBL_tavg_all)')

    # Should all MARBL diagnostics be included in the first tavg stream?
    parser.add_argument('--lMARBL_tavg_all', action='store', dest='lMARBL_tavg_all',
                        type=bool, default=False, help="Put all MARBL diagnostics in stream number 1")

    # Should MARBL's ALT_CO2 diagnostics be included in the tavg streams?
    parser.add_argument('--lMARBL_tavg_alt_co2', action='store', dest='lMARBL_tavg_alt_co2',
                        type=bool, default=False, help="Include ALT_CO2 diagnostics in streams")

    # Should lines be appended to tavg_contents_out instead of clobbering?
    parser.add_argument('--append', action='store', dest='append', default=False,
                        type=bool, help='Append output to tavg_contents_out instead of clobbering')

    return parser.parse_args()

#######################################

def _parse_line(line_in):
    """ Take a line of input from the MARBL diagnostic output and return both
        variable name and frequency. Lines that are commented out or empty
        should return None for both varname and frequency.

        Frequency is always returned as a list, although it often has just one
        element.
    """
    line_loc = line_in.split('#')[0].strip()
    # Return None, None if line is empty
    if len(line_loc) == 0:
        return None, None, None

    logger = logging.getLogger("__name__")
    line_split = line_loc.split(':')
    if len(line_split) == 1:
        logger.error("Can not determine frequency and operator from following line: '%s'" % line_in)
        sys.exit(1)
    freq = []
    op = []
    for freq_op in line_split[1].split(','):
        freq_op_split = freq_op.strip().split('_')
        if len(freq_op_split) != 2:
            logger.error("Can not determine frequency and operator from following entry: '%s'" % line_split[1])
            return None, None, None
        freq.append(freq_op_split[0])
        op.append(freq_op_split[1])
    return line_split[0].strip(), freq, op

#######################################

def _get_freq(frequency, frequency_streams):
    """ Convert MARBL frequency ('never', 'low', 'medium', 'high') to POP streams.
        Note that frequency_streams must be a list of length 3, containing low, medium,
        and high frequency stream numbers (in that order)
    """
    freq_loc = frequency.strip().lower()
    if freq_loc == 'never':
        return '#'
    elif freq_loc == 'low':
        return '%d' % frequency_streams[0]
    elif freq_loc == 'medium':
        return '%d' % frequency_streams[1]
    elif freq_loc == 'high':
        return '%d' % frequency_streams[2]
    else:
        logger = logging.getLogger("__name__")
        logger.error("Unrecognized output frequency: '%s'" % freq_loc)

#######################################

def diagnostics_to_tavg_and_operators(ecosys_diagnostics_in,
                                      MARBL_diagnostics_list_in,
                                      tavg_contents_out,
                                      MARBL_diagnostics_operator_out,
                                      append,
                                      lMARBL_tavg_all,
                                      lMARBL_tavg_alt_co2,
                                      frequency_streams):

    import os, sys, logging
    logger = logging.getLogger("__name__")
    labort = False
    processed_vars = []

    # 1. Check arguments:
    #    ecosys_diagnostics_in can not be None and must be path of an existing file
    if ecosys_diagnostics_in == None:
        logger.error("Must specific ecosys_diagnostics_in")
        labort = True
    elif not os.path.isfile(ecosys_diagnostics_in):
        logger.error("File not found %s" % ecosys_diagnostics_in)
        labort = True
    #    MARBL_diagnostics_list_in can not be None and must be path of an existing file
    if MARBL_diagnostics_list_in == None:
        logger.error("Must specific MARBL_diagnostics_list_in")
        labort = True
    elif not os.path.isfile(MARBL_diagnostics_list_in):
        logger.error("File not found %s" % MARBL_diagnostics_list_in)
        labort = True
    if labort:
        sys.exit(1)

    # 2. Read list of all MARBL diagnostics
    MARBL_diagnostics_list = []
    with open(MARBL_diagnostics_list_in, 'r') as file_in:
        MARBL_diagnostics_list = [diag.strip() for diag in file_in.readlines()]

    # Open files for output
    try:
        if append:
            outstream1 = open(tavg_contents_out, 'a')
        else:
            outstream1 = open(tavg_contents_out, 'w')
    except:
        logger.error("Can not open %s to write" % tavg_contents_out)
        sys.exit(1)
    try:
        outstream2 = open(MARBL_diagnostics_operator_out, 'w')
    except:
        logger.error("Can not open %s to write" % MARBL_diagnostics_operator_out)
        sys.exit(1)

    # Files header
    outstream1.write('#  The following diagnostics were provided via\n')
    outstream1.write('#  %s\n' % ecosys_diagnostics_in)
    outstream2.write('#  The following operators were requested via\n')
    outstream2.write('#  %s\n' % ecosys_diagnostics_in)

    # Read ecosys_diagnostics_in line by line, convert each line to tavg content
    with open(ecosys_diagnostics_in, 'r') as file_in:
        all_lines = file_in.readlines()
    for line in all_lines:
        varname, frequency, operator = _parse_line(line.strip())
        # Continue to next line in the following circumstances
        # i.  varname = None
        if varname == None:
            continue
        # ii. Skip ALT_CO2 vars unless explicitly requested
        if (not lMARBL_tavg_alt_co2) and ("ALT_CO2" in varname):
            continue

        # Abort if varname has already appeared in file
        if varname in processed_vars:
            logger.error("'%s' appears in %s multiple times" % (varname, ecosys_diagnostics_in))
            sys.exit(1)
        processed_vars.append(varname)

        # tavg_contents
        for n, freq in enumerate(frequency):
            if lMARBL_tavg_all:
                use_freq = '1'
            else:
                use_freq = _get_freq(freq, frequency_streams)
            if n == 0:
                outstream1.write('%s  %s\n' % (use_freq, varname))
            else:
                outstream1.write('%s  %s_%d\n' % (use_freq, varname, n+1))

        # MARBL_diagnostics_operator
        if varname in MARBL_diagnostics_list:
            if lMARBL_tavg_all:
                use_op = ', '.join(['average']*len(operator))
            else:
                use_op = ', '.join(operator)
            if use_op != 'none':
                outstream2.write('%s : %s\n' % (varname, use_op))

    # File footer
    outstream1.write('#  end of diagnostics from\n# %s\n' % ecosys_diagnostics_in)

    # Close streams
    outstream1.close()
    outstream2.close()

#######################################

if __name__ == "__main__":
    # Parse command line arguments
    args = _parse_args()

    import logging
    logging.basicConfig(format='%(levelname)s (%(funcName)s): %(message)s', level=logging.DEBUG)

    # call diagnostics_to_tavg()
    diagnostics_to_tavg_and_operators(args.ecosys_diagnostics_in,
                                      args.MARBL_diagnostics_list_in,
                                      args.tavg_contents_out,
                                      args.MARBL_diagnostics_operator_out,
                                      args.append,
                                      args.lMARBL_tavg_all,
                                      args.lMARBL_tavg_alt_co2,
                                      [args.low_frequency_stream,
                                       args.medium_frequency_stream,
                                       args.high_frequency_stream])
