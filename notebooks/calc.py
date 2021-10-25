import pop_tools
import xarray as xr


def _get_tb_name_and_tb_dim(ds):
    """return the name of the time 'bounds' variable and its second dimension"""
    assert "bounds" in ds.time.attrs, 'missing "bounds" attr on time'
    tb_name = ds.time.attrs["bounds"]
    assert tb_name in ds, f'missing "{tb_name}"'
    tb_dim = ds[tb_name].dims[-1]
    return tb_name, tb_dim


def center_time(ds):
    """make time the center of the time bounds"""
    ds = ds.copy()
    attrs = ds.time.attrs
    encoding = ds.time.encoding
    tb_name, tb_dim = _get_tb_name_and_tb_dim(ds)

    ds["time"] = ds[tb_name].compute().mean(tb_dim).squeeze()
    attrs["note"] = f"time recomputed as {tb_name}.mean({tb_dim})"
    ds.time.attrs = attrs
    ds.time.encoding = encoding
    return ds


def add_grid_variables(
    ds,
    grid_name="POP_gx1v7",
    grid_vars=["TAREA", "KMT", "REGION_MASK", "dz"],
    model="pop",
    mom_static_file="""/glade/scratch/mlevy/archive/mom_hybrid_z
                       /ocn/hist/mom_hybrid_z.mom6.static.nc""",
    mom_vertical_grid_file="""/glade/scratch/mlevy/archive/mom_oob.002
                              /ocn/hist/mom_oob.002.mom6.h_bgc_monthly_z_0014_03.nc""",
    ):

    if model == "pop":
        grid_ds = pop_tools.get_grid(grid_name)[grid_vars]
        grid_ds["z_t"] = ds.z_t

    elif model == "mom":
        grid_ds = xr.open_dataset(mom_static_file)[grid_vars]

    merged_ds = xr.merge([ds, grid_ds])

    if "z_l" in merged_ds:
        merged_ds = merged_ds.rename({"z_l": "z_t"})
        merged_ds["dz"] = xr.open_dataset(mom_vertical_grid_file)["z_i"].diff("z_i")

    return merged_ds


def global_mean(ds, normalize=True, include_ms=False, region_mask=None, model="pop"):
    """
    Compute the global mean on a POP or MOM dataset.
    Return computed quantity in conventional units.
    """

    if model == "pop":
        horizontal_dims = ("nlat", "nlon")
        area_field = "TAREA"
        land_sea_mask = "KMT"

    elif model == "mom":
        horizontal_dims = ("yh", "xh")
        area_field = "area_t"
        land_sea_mask = "wet"
        include_ms = True

    compute_vars = [
        v for v in ds if "year" in ds[v].dims and horizontal_dims == ds[v].dims[-2:]
    ]

    other_vars = list(set(ds.variables) - set(compute_vars))

    if include_ms:
        surface_mask = ds[area_field].where(ds[land_sea_mask] > 0).fillna(0.0)
    else:
        surface_mask = ds[area_field].where(ds.REGION_MASK > 0).fillna(0.0)

    if region_mask is not None:
        surface_mask = surface_mask * region_mask

    masked_area = {
        v: surface_mask.where(ds[v].notnull()).fillna(0.0) for v in compute_vars
    }

    with xr.set_options(keep_attrs=True):

        dso = xr.Dataset(
            {v: (ds[v] * masked_area[v]).sum(horizontal_dims) for v in compute_vars}
        )
        if normalize:
            dso = xr.Dataset(
                {v: dso[v] / masked_area[v].sum(horizontal_dims) for v in compute_vars}
            )

        return xr.merge([dso, ds[other_vars]]).drop(
            [c for c in ds.coords if ds[c].dims == horizontal_dims]
        )


def global_integral(ds, normalize=True, include_ms=False, region_mask=None):
    """
    Compute the global mean on a POP dataset.
    Return computed quantity in conventional units.
    """

    compute_vars = [
        v for v in ds if "year" in ds[v].dims and ("nlat", "nlon") == ds[v].dims[-2:]
    ]

    other_vars = list(set(ds.variables) - set(compute_vars))

    if include_ms:
        surface_mask = ds.TAREA.where(ds.KMT > 0).fillna(0.0)
    else:
        surface_mask = ds.TAREA.where(ds.REGION_MASK > 0).fillna(0.0)

    if region_mask is not None:
        surface_mask = surface_mask * region_mask

    masked_area = {
        v: surface_mask.where(ds[v].notnull()).fillna(0.0) for v in compute_vars
    }

    with xr.set_options(keep_attrs=True):

        dso = xr.Dataset(
            {v: (ds[v] * masked_area[v]).sum(["nlat", "nlon"]) for v in compute_vars}
        )
        if normalize:
            dso = xr.Dataset(
                {v: dso[v] / masked_area[v].sum(["nlat", "nlon"]) for v in compute_vars}
            )

        return xr.merge([dso, ds[other_vars]]).drop(
            [c for c in ds.coords if ds[c].dims == ("nlat", "nlon")]
        )
