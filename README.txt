# project
Parses Java 11 API and generates the CSV file containing the information in a table format

module|URL|description|package|URL|description|type|name|URL|description

# how to run

1. build docker image
docker build -t python_parser .
2. run docker container
docker run -it --rm -v c:/tools/projects/java-doc-api-dictionary:/home/python-folder python_parser
3. terminated immediately as we don't need running container at all

