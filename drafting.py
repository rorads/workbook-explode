import pandas as pd
import re

workbook_file = pd.ExcelFile("data/constant-multiple-simple.xlsx")

dfs = {sheet_name: workbook_file.parse(sheet_name) for sheet_name in workbook_file.sheet_names}

dfs['Sheet1']


# group 1 = pre square brackets slug, group 2 = comma separated K:V pairs
CONSTANTS_PATTERN = re.compile(r"([^\[]*)\[([^\]]*)\]")

WILDCARDS_PATTERN = re.compile(r"([^\*]*)\*([^\*]*)")

constant1 = "element/subelement/0/value[FTE:1]"
constant2 = "element/subelement/0/value[FTE:12, Value:45]"
wildcard1 = "element/subelement/*/value"

wildcard1.split("*")[0]

# testing

constant_match1 = CONSTANTS_PATTERN.search(constant1)
constant_match2 = CONSTANTS_PATTERN.search(constant2)
wildcard_match = WILDCARDS_PATTERN.search(wildcard1)

print(constant_match1.group(1) + " :: " + constant_match1.group(2))
print(constant_match2.group(1) + " :: " + constant_match2.group(2))
print(wildcard_match.group(1) + " :: " + wildcard_match.group(2))
