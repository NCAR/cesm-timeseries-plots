import metpy
import xarray as xr

def convert_units(ds, variable, out_unit, in_unit=None):
    """Makes use of MetPy and Pint to handle unit conversion"""
    
    if not (ds[variable].units or in_unit):
        raise 'Missing units - must supply input units'
    
    # Use Metpy/Pint to handle the unit conversion
    converted_array = ds.metpy.parse_cf(variable).metpy.unit_array.to(out_unit)
    
    # Extract the actual values and out units
    converted_values = converted_array.m
    converted_units = str(converted_array.units)
    
    # Grab the variable attribute and dimension information
    in_attrs = ds[variable].attrs
    in_dims = ds[variable].dims
    
    # 
    ds = ds.assign({variable:(in_dims, converted_values)})
    ds[variable].attrs = in_attrs
    ds[variable].attrs['units'] = converted_units
    return ds

def convert_units_dict(ds, variable_dict):
    """Handles unit converstion using a variable dictionary, formatted with the variable name as the key with each key having an out_units variable"""
    
    for variable in variable_dict.keys():
        ds = convert_units(ds, variable, variable_dict[variable]['out_units'])
        
    return ds