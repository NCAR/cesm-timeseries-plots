import metpy
import xarray as xr


def convert_units(ds, variable, out_unit, in_unit=None, molecular_scaling_factor=None):
    """Makes use of MetPy and Pint to handle unit conversion"""

    # Double check this - assert statement (some sort of exception)
    if not (ds[variable].units or in_unit):
        raise ValueError("Missing units - must supply input units")

    # Convert to base units
    original_array = ds.metpy.parse_cf(variable).metpy.unit_array.to_base_units()

    if molecular_scaling_factor:
        original_array * molecular_scaling_factor

    # Use Metpy/Pint to handle the unit conversion
    converted_array = original_array.to(out_unit)

    if molecular_scaling_factor:
        converted_array * molecular_scaling_factor

    # Extract the actual values and out units
    converted_values = converted_array.m
    converted_units = str(converted_array.units)

    # Grab the variable attribute and dimension information
    in_attrs = ds[variable].attrs
    in_dims = ds[variable].dims

    #
    ds = ds.assign({variable: (in_dims, converted_values)})
    ds[variable].attrs = in_attrs
    ds[variable].attrs["units"] = converted_units
    return ds


def _clean_units(units):
    """replace some troublesome unit terms with acceptable replacements"""
    replacements = {
        "kgC": "kg",
        "gC": "g",
        "gC13": "g",
        "gC14": "g",
        "gN": "g",
        "unitless": "1",
        "years": "common_years",
        "yr": "common_year",
        "meq": "mmol",
        "neq": "nmol",
    }
    units_split = re.split(r"( |\(|\)|\^|\*|/|-[0-9]+|[0-9]+)", units)
    units_split_repl = [
        replacements[token] if token in replacements else token for token in units_split
    ]
    return "".join(units_split_repl)


def convert_units_dict(ds, variable_dict):
    """Handles unit converstion using a variable dictionary, formatted with the variable name as the key with each key having an out_units variable"""

    for variable in variable_dict.keys():
        ds = convert_units(ds, variable, variable_dict[variable]["units_out"])

    return ds
