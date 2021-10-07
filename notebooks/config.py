import yaml

with open("analysis_config.yml", mode="r") as fptr:
    analysis_config = yaml.safe_load(fptr)

# Read in the variable dictionary
variable_dict = analysis_config['variables']

# Grab a list of variables
variable_list = list(variable_dict.keys())

# Add the vertical transformations to the list of variables
all_variables = variable_dict
all_variables.update(analysis_config['vertical_transformations'])

# Determine which variables need to converted
variables_to_convert = {}
for variable in all_variables.keys():
    if all_variables[variable]['out_units']:
        variables_to_convert.update({variable:all_variables[variable]})

