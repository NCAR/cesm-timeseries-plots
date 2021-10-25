
import numpy as np
import xarray as xr
import yaml

with open("region_definitions.yml", mode="r") as fptr:
    region_defs = yaml.safe_load(fptr)


def _default_merge_dict():
    return region_defs["default"]


def generate_3D_mask(
    basins, ds, lon_name="lon", lat_name="lat", merge_dict=None,
):
    """Combine geographical basins (from regionmask) to larger ocean basins.
    Parameters
    ----------
    basins : regionmask.core.regions.Regions object
        Loaded basin data from regionmask, e.g. 
        `import regionmask;basins =
        regionmask.defined_regions.natural_earth.ocean_basins_50`
    ds : xr.Dataset
        Input dataset on which to construct the mask
    lon_name : str, optional
        Name of the longitude coordinate in `ds`, defaults to `lon`
    lat_name : str, optional
        Name of the latitude coordinate in `ds`, defaults to `lat`
    merge_dict : dict, optional
        dictionary defining new aggregated regions (as keys) and 
        the regions to be merge into that region as as values (list of names).
        Defaults to large scale ocean basins defined by 
        `cmip6_preprocessing.regionmask.default_merge_dict`
    Returns
    -------
    mask : xr.DataArray
        The mask contains ascending numeric value for each key 
        ( merged region) in `merge_dict`.
        
        When the default is used the numeric values 
        correspond to the following regions:
        * 0: North Atlantic
        * 1: South Atlantic
        * 2: North Pacific
        * 3: South Pacific
        * 4: Maritime Continent
        * 5: Indian Ocean
        * 6: Arctic Ocean
        * 7: Southern Ocean
        * 8: Black Sea
        * 9: Mediterranean Sea
        *10: Red Sea
        *11: Caspian Sea
    """
    mask = basins.mask(ds, lon_name=lon_name, lat_name=lat_name)

    if merge_dict is None:
        merge_dict = _default_merge_dict()

    dict_keys = list(merge_dict.keys())
    number_dict = {k: None for k in dict_keys}
    merged_basins = []
    for ocean, small_basins in merge_dict.items():
        try:
            ocean_idx = basins.map_keys(ocean)
        except (KeyError):
            # The ocean key is new and cant be found in the 
            # previous keys (e.g. for Atlantic full or maritime continent)
            ocean_idx = mask.max().data + 1
        number_dict[ocean] = ocean_idx
        if small_basins:
            for sb in small_basins:
                sb_idx = basins.map_keys(sb)
                # set the index of each small basin to the ocean value
                mask = mask.where(mask != sb_idx, ocean_idx)
                merged_basins.append(sb)

    # reset the mask indicies to the order of the passed dictionary keys
    mask_reordered = xr.ones_like(mask.copy()) * np.nan
    for new_idx, k in enumerate(dict_keys):
        old_idx = number_dict[k]
        mask_reordered = mask_reordered.where(mask != old_idx, new_idx)

    # Convert to 3D
    region_list = []
    mask_reordered += 1
    for region in np.unique(mask_reordered.values):
        if region > -1:
            region_list.append(
                (
                    mask_reordered.where(mask_reordered == region) / mask_reordered
                ).expand_dims("region")
            )
    merged_ds = xr.concat(region_list, dim="region")
    merged_ds["region"] = list(merge_dict.keys())
    merged_ds.attrs["mask_name"] = "default_mask"
    return mask_reordered.fillna(0)
