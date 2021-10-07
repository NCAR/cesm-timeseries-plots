import hvplot
import hvplot.xarray

def time_depth_plot(ds, variable, vertical_dim='z_t', ylim=(1000, 0), levels=20, cmap='inferno', vmin=None, vmax=None, log_cbar=False):
    plot = (ds[variable].hvplot.contourf(x='year', y=vertical_dim, ylim=ylim, levels=levels, cmap=cmap, height=400, width=800, hover=False, clim=(vmin, vmax), logz=log_cbar) *\
            ds[variable].hvplot.contourf(x='year', y=vertical_dim, ylim=ylim, levels=levels, cmap=cmap, height=400, width=800, hover=False, clim=(vmin, vmax), logz=log_cbar))
    return plot

def line_plot(ds, variable, ylim=None):
    plot = ds[variable].hvplot.line(x='year', by='case', ylim=ylim)
    return plot