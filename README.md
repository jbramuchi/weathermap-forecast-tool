# weathermap-forecast-tool
Reporting tool, pulls weather API data for cities , then compiles on google sheets as needed



This automation served as a reporting tool for a client at my data science internship.
All of the data transformations are done in a google spreadsheet, external of this program.

A lookup table of zipcodes and corresponding latitudes and longitudes, from google sheets, are processed into the automation. Then, the
information is loaded into multiple tasks, formatted as individual requests to OpenWeatherMap's API. The requests are then thrown into an
asynchronous loop that runs them in parallel.

The information is pulled, formatted, then batch-inserted into a different corresponding section in the same google sheets table to be
dealt with as desired.
