import xarray as xr
import pop_tools

def _get_tb_name_and_tb_dim(ds):
    """return the name of the time 'bounds' variable and its second dimension"""
    assert 'bounds' in ds.time.attrs, 'missing "bounds" attr on time'
    tb_name = ds.time.attrs['bounds']        
    assert tb_name in ds, f'missing "{tb_name}"'    
    tb_dim = ds[tb_name].dims[-1]
    return tb_name, tb_dim


def _gen_time_weights(ds):
    """compute temporal weights using time_bound attr"""    
    tb_name, tb_dim = _get_tb_name_and_tb_dim(ds)
    chunks_dict = _get_chunks_dict(ds[tb_name])
    del chunks_dict[tb_dim]
    return ds[tb_name].compute().diff(tb_dim).squeeze().astype(float).chunk(chunks_dict)
    
    
def center_time(ds):
    """make time the center of the time bounds"""
    ds = ds.copy()
    attrs = ds.time.attrs
    encoding = ds.time.encoding
    tb_name, tb_dim = _get_tb_name_and_tb_dim(ds)
    
    ds['time'] = ds[tb_name].compute().mean(tb_dim).squeeze()
    attrs['note'] = f'time recomputed as {tb_name}.mean({tb_dim})'
    ds.time.attrs = attrs
    ds.time.encoding = encoding
    return ds

def add_grid_variables(ds, grid_name='POP_gx1v7', grid_vars=['TAREA', 'KMT', 'REGION_MASK', 'dz']):
    
    grid_ds = pop_tools.get_grid(grid_name)[grid_vars]
    grid_ds['z_t'] = ds.z_t
    
    return xr.merge([ds, grid_ds])

def global_mean(ds, normalize=True, include_ms=False, region_mask=None):
    """
    Compute the global mean on a POP dataset. 
    Return computed quantity in conventional units.
    """

    compute_vars = [
        v for v in ds 
        if 'year' in ds[v].dims and ('nlat', 'nlon') == ds[v].dims[-2:]
    ]
    
    other_vars = list(set(ds.variables) - set(compute_vars))

    if include_ms:
        surface_mask = ds.TAREA.where(ds.KMT > 0).fillna(0.)
    else:
        surface_mask = ds.TAREA.where(ds.REGION_MASK > 0).fillna(0.)
    
    if region_mask is not None:
        surface_mask = surface_mask * region_mask
    
    masked_area = {
        v: surface_mask.where(ds[v].notnull()).fillna(0.) 
        for v in compute_vars
    }

    
    with xr.set_options(keep_attrs=True):
        
        dso = xr.Dataset({
            v: (ds[v] * masked_area[v]).sum(['nlat', 'nlon'])
            for v in compute_vars
        })
        if normalize:
            dso = xr.Dataset({
                v: dso[v] / masked_area[v].sum(['nlat', 'nlon'])
                for v in compute_vars
            })            
        else:
            for v in compute_vars:
                if v in variable_defs.C_flux_vars:
                    dso[v] = dso[v] * nmols_to_PgCyr
                    dso[v].attrs['units'] = 'Pg C yr$^{-1}$'
                
        return xr.merge([dso, ds[other_vars]]).drop(
            [c for c in ds.coords if ds[c].dims == ('nlat', 'nlon')]
        )