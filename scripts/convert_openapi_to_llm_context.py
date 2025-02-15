OUTPUT_PATH = 'backend/llm_context/docs' # Path to write the generated context files

#ai! 
# create a method to convert openapi descriptions into llm context files
# input: openapi file, api_name
# read the openapi description from a file
# convert each operation into a context file, skip the ones that match our skipFilter list of words
# write the context files to the output path / {api_name} / {api_name}_{operationId}.md
# each file should have the descriptiona and response type 
