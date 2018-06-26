# Drafting: Modelling Indicators in CoVE Workbooks

This repository is a starting point for developers within Open Data Services Cooperative to either pickup and run with, or use as a verbose example of how not to solve this problem.

The problem has been outlined by @timgdavies in a gist which I've reproduced below. All I've done so far is create a skeletal outline of how I'd approach this, and funtionality for the '*' wildcard column headings. The [key:value] constants haven't been worked through yet, and I've peppered the code with `# TODO:` comments where I think there is more functionality needed (for instance, validation of workbooks before attempting to explode their special columns.

Any questions, let me know. I'm going to assume that this repo won't be needed for more than a few weeks, so once the relevant code has been copied over (or pointed and laughted at), I'll remove it from GH.

---

# Tim's Gist 

This document contains preliminary remarks on modelling indicators in spreadsheets and schema to support the work of the Global Coffee Platform and Social Economy Data Lab project.

## Requirements

We want to capture data about **indicators**.

An indicator consists of a **measure** and a set of **dimensions**.

Indicators attach to **entities** like organisations, localities or investments. 

Indicators may have particular data types or validation rules related to them.

Indicators need to be clearly and accessiblity documented

## The structural challenge

An indicator might be "Number of staff". 

We might state that Open Data Services Co-op has 14 staff. 

A spreadsheet about organisations and their numbers of staff might represent this as:

| Organisation | Number of staff |
| ------------ | --------------- |
| Open Data Services Co-op | 14 |

To make this work with flatten tool, we might expand this to:

| org/name | org/id | org/indicators/0/value |
| ----------------- | --------------- | ------------------------------- |
| Open Data Services Co-op | GB-COH-09506232 | 14 |

**But**, this leaves quite a lot of information implicit. 

* What period does this measure cover? 
* How is the measure defined?

The JSON representation of the above would be:

    {
        "org": {
            "id":"GB-COH-09506232",
            "name":"Open Data Services Co-op",
            "indicators":[
                {
                    "value":14
                }
            ]
        }
    }

But we really need something at least like:

    {
      "org": {
            "id":"GB-COH-09506232",
            "name":"Open Data Services Co-op",
            "indicators":[
                {
                    "indicatorCode":"FTE",
                    "value":14,
                    "date":"2018-04-19"
                }
            ]
        }
    }

Which would be OK in a spreadsheet where each indicator is it's own row, and we could have:

| org/name | org/id | org/indicators/0/code | org/indicators/0/date | org/indicators/0/value |
| ---------| -------- | --------------- | ------------------------------- | --------------- |
| Open Data Services Co-op | GB-COH-09506232 | FTE | 2018-04-19 | 14 | 

But in many of the spreadsheets we've been, users prefer to lay information out with a metric in each column, such as:

| Organisation Name | Date measured | FTE Staff | Part-time staff (total) | Volunteers |
|-------------------|---------------|-----------|-------------------------|------------|
| Open Data Services Co-op | 2018-04-09 | 14 | 6 | 0 |

It would be good if we can maintain structures like this, whilst marking them up to generate clear structured data. 

In doing so we have to be aware that:

* Users often create filters or sort spreadsheets, making hidden rows and positional markup difficult to maintain

### A proposal: data structures

We could create a pre-processor for flatten-tool which **expands out** the additional contextual columns for each indicator without requiring that the columns are included in the original.

This would support two additional syntaxes.

**(1) Adding a constant value to every row**

When [property:value] is included on the end of a field path in the header row, an additional column must be created that has a field path ending in 'property' and the value filled down in every row in which the source column has a value.

For example:

| org/id | org/indicators/0/value[code:FTE] | org/indicators/1/value[code:Volunteers] |
| ----------------|-------------|--------------|
| GB-COH-09506232 | 14 | 0 |
| GB-COH-05381958 |  | 2 |

Would become:

| org/id | org/indicators/0/code | org/indicators/0/value | org/indicators/1/code | org/indicators/1/value[code:Volunteers] |
| ----------------|-------------|--------------|--------------|--------------|
| GB-COH-09506232 | FTE | 14 | Volunteers | 0 |
| GB-COH-05381958 | | | Volunteers | 2 |

(Note the two new columns created, and filled where their paired column had a value).

**(2) Adding a constant value to every column**

When a column path exists with a wildcard in place of an array integer, a column must be created for each following integer that could be substituted in for the wildcard, processing across the table until the final such column OR until the same wildcard column is encountered again. 

For example:

| org/id | org/indicators/*/year | org/indicators/0/value | org/indicators/1/value |
|--------------|---------|--------|----------|
| GB-COH-09506232 | 2017 | 14 | 0 | 
| GB-COH-05381958 | 2018 | 2 | |

Would become:

| org/id | org/indicators/0/year | org/indicators/0/value | org/indicators/1/year | org/indicators/1/value |
|--------------|---------|--------|----------|----------|
| GB-COH-09506232 | 2017 | 14 | 2017 | 0 | 
| GB-COH-05381958 | 2018 | 2 | 2018 | |

(Note the year column, now given for each wildcard field)

The rule about only applying this expansion until such time as a second wildcard column is found is illustrated below:

| org/id | org/indicators/*/year | org/indicators/0/value | org/indicators/1/value | org/indicators/*/year | org/indicators/2/value | org/indicators/*/year | org/indicators/3/value
|--------------|---------|--------|----------|----------|----------|----------|----------|
| GB-COH-09506232 | 2017 | 14 | 0 | - | 5 | 2015 | 1 | 
| GB-COH-05381958 | 2018 | 2 | | - | 5 | 2016 | 2 |

Which would expand to:

| org/id | org/indicators/0/year | org/indicators/0/value | org/indicators/1/year | org/indicators/1/value | org/indicators/2/value | org/indicators/3/year | org/indicators/3/value |
|--------------|---------|--------|----------|----------|----------|----------|----------|
| GB-COH-09506232 | 2017 | 14 | 2017 | 0 | 5 | 2015 | 1 |
| GB-COH-05381958 | 2018 | 2 | 2018 | | 5 | 2016 | 2 |

Note here that the use of a blank (shown with '-') `indicators/*/year` column after `indicators/1/value` means no year column has been created for the `indicators/2/value`, but then the next use of `indicators/*/year` sets a new year for the columns that follow. 

**Putting it together**

Combined, these two expansions should make it possible to generate rich data from terse spreadsheets that match how data is often organised. There are similarities here to the approach taken by HXL, but rather than indicating the concepts represented by columns, we are looking to support conversion into tree structured data.

For example, the table below:

| org/name | org/id | org/indicators/*/year | org/indicators/0/value[code:FTE] | org/indicators/1/value[code:Volunteers] | org/indicators/2/value[code:Turnover] | 
|-------------------|-----------------|------|-----------------|------------|----------|
| **Organisation Name** | **Organisation ID** | **Year** | **Employees (FTE)** | **Volunteers** | **Turnover** |
| Open Data Services Co-operative |  GB-COH-09506232 | 2018 | 12 | 0 | 500000 | 
| Practical Participation Ltd | GB-COH-05381958 | 2017 | 2 | 1 | 100000 |

should expand to:

```json
    [
        {
            "org": {
                "name": "Open Data Services Co-operative",
                "id": "GB-COH-09506232",
                "indicators": [
                    {
                        "year": "2018",
                        "code": "FTE",
                        "value": "12"
                    },
                    {
                        "code": "Volunteers",
                        "year": "2018",
                        "value": "0"
                    },
                    {
                        "year": "2018",
                        "code": "Turnover",
                        "value": "500000"
                    }
                ]
            }
        },
        {
            "org": {
                "name": "Practical Participation Ltd",
                "id": "GB-COH-05381958",
                "indicators": [
                    {
                        "year": "2017",
                        "code": "FTE",
                        "value": "2"
                    },
                    {
                        "code": "Volunteers",
                        "year": "2017",
                        "value": "1"
                    },
                    {
                        "year": "2017",
                        "code": "Turnover",
                        "value": "100000"
                    }
                ]
            }
        }
    ]
```    

## Data validation challenges

The second challenge we face relates to **indicator validation** and documentation. 

For example, we might know that:

* FTE Staff indicators should be given by a number, and should have period value;
* A turnover indicaitor should be a number **and** that it should also have a currency value specified;

We therefore need a way to:

* Represent;
* Document; and
* Validate

requirements for indicators? 

JSON Schema offers us an approach to this, allowing us to create a small block of schema for each indicator. For example:

**FTE Employees Indicator**

```json
    {
        "type":"object",
        "title":"Employees (FTE)",
        "description":"Number of employees, full-time equivalent.",
        "properties":{
            "code":{
                "type":"string",
                "enum":["FTE"]
            },
            "date":{
                "type":"string",
                "title":"Period",
                "description":"The date may be provided as  YYYY, YYYY-MM, or YYYY-MM-DD"
            },
            "value":{
                "type":"number"
            }
        }
    }
```

**Turnover indicator**

```json
    {
        "type":"object",
        "title":"Turnover",
        "description":"Turnover in the calendar year starting on the given date.",
        "properties":{
            "code":{
                "type":"string",
                "enum":["Turnover"]
            },
            "date":{
                "type":"string",
                "title":"Start date of 12 month period",
                "description":"The date may be provided as  YYYY, YYYY-MM, or YYYY-MM-DD"
            },
            "value":{
                "type":"number"
            },
            "currency":{
                "type":"string",
                "title":"Currency",
                "description":"An ISO Currency String",
                "enum":["USD","GBP","EUR"]
            },
            "required":["code","value","currency","date"]
        }
    }
```    

These can be combined into an overall JSON schema using the `anyOf` property. 


## Indicator documentation

Adam Locker at the Food Standards Agency has written a [useful primer on documenting metrics](https://github.com/adamlocker/Metric_Templating)
