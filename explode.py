import pandas as pd
import re

######################################
# Test is at the bottom of this file #
######################################

def process_workbook(input_filepath, output_filepath="data/output.xlsx"):
    """
    Given a .xlsx workbook which is valid for conversion via CoVE, this method
    will recognise special columns to asign constant values for elements, or
    establish special wildcard columns which can be applied to subsequent
    instances of a given element.


    Args:
        input_filepath (str): The CoVE workbook to be pre-processed.
        output_filepath (str): The destination for the pre-processed workbook.

    Returns:
        bool: The return value. True for success, False otherwise.

    """

    writer = pd.ExcelWriter(output_filepath)

    # return a dict with keys = tab names, values = tab dataframes
    workbook_dict = setup_workbook(input_filepath)

    # throw an exception if column values are broken otherwise return true.
    validate_workbook(workbook_dict)

    # parse all columns and explode the wildcard values horizontally
    exploded_horizontal = explode_horizontal(workbook_dict)

    # parse all columns and explode the constants vertically
    exploded_vertical = explode_vertical(exploded_horizontal)

    write_to_file(exploded_vertical, writer)


def write_to_file(workbook_dictionary, writer):

    for name, cells_df in workbook_dictionary.items():
        cells_df.to_excel(writer, name, index=False)
    writer.save()


def setup_workbook(input_filepath):
    """
    Return a dict with keys = sheet names, values = sheet dataframes

    Args:
        input_filepath (str): a given workbook

    Returns:
        dict: a dictionary of the workbooks tabs as pandas data frames
    """

    workbook_file = pd.ExcelFile(input_filepath)

    # TODO: parse the Meta tab and remove human headings if there's a 'skipRows' declaration

    workbook_dict = {sheet_name: workbook_file.parse(sheet_name) for sheet_name in workbook_file.sheet_names}

    return workbook_dict


def validate_workbook(workbook_dictionary):
    """
    Takes a workbook dictionary and validates the non-commented tabs to check
    that each one is compatible with the pre-processor i.e. verticle explosion
    commands must be comma seperable

    Args:
        workbook_dictionary (dict): a dictionary of workbook represented in
        pandas data frames

    Returns:
        bool: True if successful, otherwise an exception is thrown.
    """

    # TODO: add conditions which break the pre-processor and make this exception throwing

    # If there are duplicate columns which aren't wildcards If there are columns ending in ".\d+" - this will break
    # the suffix clipping which happens in the horizontal explosion.

    return True


def explode_horizontal(workbook_dictionary):
    """
    Checks for each non-commented tab in a workbook dicitonary, whether
    a wildcard column is present (of the form "element/subelement/*/value"). For
    each instance of a wildcard column, the column is replicated for each
    instance of the base element to the right of the wildcard unless another wildcard is
    found.

    TODO: the use of a 'null' value to 'switch off' the wildcard will need to be
    incorporated

    Args:
        workbook_dictionary (dict): a dictionary of workbook represented in
        pandas data frames

    Returns:
        dict: a dictionary of the workbooks tabs as pandas data frames, with
        wildcard columns exploded out.
    """

    # Matches "element/subelement/*/value" with capture groups before and
    # after the asterisk
    wildcards_pattern = re.compile(r"([^\*]*)\*([^\*]*)")

    # Used to remove the ".1", ".2" added by pandas to the end of duplicate
    # wildcard rows
    suffix_pattern = re.compile(r"([^\n]*)\.\d+")

    for sheet_name, sheet_frame in workbook_dictionary.items():

        # set up a wildcard stack
        wildcards = {}

        # ignore commented sheets
        if sheet_name.startswith("#"):
            continue
        else:
            for column in sheet_frame:

                # if it's a wildcard, put it in the dict - this will overwrite any previous identical wildcards
                match = wildcards_pattern.search(str(column))
                if match:

                    # remove the suffix
                    suffix_match = suffix_pattern.search(column)
                    if suffix_match:
                        column_key = suffix_match.group(1)
                    else:
                        column_key = column

                    wildcards[column_key] = sheet_frame[column]

                    sheet_frame.drop(column, axis=1, inplace=True)

                # if it's not a wildcard, check if it matches any previous wildcards
                # and if so, explode their value out into this column's signature
                else:
                    for wildcard, value in wildcards.items():

                        # create a pattern from the wildcard found, and check if the current column matches it
                        reverse_wildcard_string = r"({}\d+)({})".format(wildcard.split("*")[0], r"/[^\n]*?")
                        reverse_wildcard_pattern = re.compile(reverse_wildcard_string)
                        reverse_match = reverse_wildcard_pattern.search(column)
                        if reverse_match:
                            new_column = "{}{}".format(reverse_match.group(1), wildcard.split("*")[1])
                            sheet_frame[new_column] = value
                            # TODO check if this new column already exists. If
                            # it does, throw an error and explain that there's
                            # a dupliation.

    return workbook_dictionary

def explode_vertical(workbook_dictionary):
    """
    Checks for each non-commented tab in a workbook dicitonary, whether
    a constant heading is present (of the form
    "element/subelement/0/value[FTE:1]"). For each instance of a constant
    column, a new column is created for each value (there can be multiple
    separated by comma), applied to the parent element.

    Args:
        workbook_dictionary (dict): a dictionary of workbook represented in
        pandas data frames

    Returns:
        dict: a dictionary of the workbooks tabs as pandas data frames, with
        wildcard columns exploded out.
    """

    # group 1 = pre square brackets slug, group 2 = comma separated K:V pairs
    constants_pattern = re.compile(r"([^\[]*)\[([^\]]*)\]")

    for sheet_name, sheet_frame in workbook_dictionary.items():

        constant_dict = {}

        # ignore commented sheets
        if sheet_name.startswith("#"):
            continue
        else:
            for column in sheet_frame:

                # if it's got constants in it, then explode it
                match = constants_pattern.search(str(column))

                if match:

                    # Separate comma separated args into a dictionary of k:v pairs
                    arg_dict = dict(re.findall(r'(\S+):(".*?"|\S+)', match.group(2)))

                    # for each k:v pair, add a column which is the original column
                    # minus everything after the last "/", plus the key. All of the
                    # values in that column will be set to v

                    for key, value in arg_dict.items():

                        # turns "element/subelement/0/value" into element/subelement/0/,
                        # then adds the key after it
                        initial_new_heading_slug = re.search(r'(.*?)[^/]+\Z',match.group(1)).group(1)
                        new_column_heading = initial_new_heading_slug + key
                        constant_dict[new_column_heading] = value

                    sheet_frame.rename(columns={str(column): match.group(1)}, inplace=True)

            # inserts the value for all rows
            for new_col, new_val in constant_dict.items():
                sheet_frame[new_col] = [new_val] * len(sheet_frame)

    return workbook_dictionary

# TESTING
process_workbook('data/constant-multiple-simple.xlsx', 'data/output.xlsx')
