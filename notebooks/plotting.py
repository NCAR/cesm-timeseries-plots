import hvplot as hv
import panel as pn
import hvplot.xarray

def time_depth_plot(ds, variable, vertical_dim='z_t', ylim=(1000, 0), levels=20, cmap='inferno', vmin=None, vmax=None, log_cbar=False):
    plot = (ds[variable].hvplot.contourf(x='year', y=vertical_dim, ylim=ylim, levels=levels, cmap=cmap, height=400, width=800, hover=False, clim=(vmin, vmax), logz=log_cbar, clabel=f'{ds[variable].units}') *\
            ds[variable].hvplot.contourf(x='year', y=vertical_dim, ylim=ylim, levels=levels, cmap=cmap, height=400, width=800, hover=True, clim=(vmin, vmax), logz=log_cbar, attr_labels=True))
    out_title = f'## {ds[variable].long_name} ({variable})'
    panel = pn.Column(pn.pane.Markdown(out_title, align="start"), plot)
    return panel

def line_plot(ds, variable, ylim=None):
    plot = ds[variable].hvplot.line(x='year', by='case', ylim=ylim)
    out_title = f'## {ds[variable].long_name} ({variable})'
    panel = pn.Column(pn.pane.Markdown(out_title, align="start"), plot)
    return panel

def generate_time_depth_plots(ds, variable_dict, vertical_dim='z_t', ylim=(1000, 0), levels=20, cmap='inferno', vmin=None, vmax=None, log_cbar=False):
    
    plot_list = []
    for variable in variable_dict.keys():
        if (vertical_dim in ds[variable].dims) and (variable != vertical_dim):
            plot_list.append(time_depth_plot(ds, variable, vertical_dim, ylim, levels, cmap, vmin, vmax, log_cbar))
            
    out_panel = pn.Column()
    for plot in plot_list:
        out_panel+=plot
        
    return out_panel

def generate_full_depth_average_plots(ds, variable_dict, vertical_dim='z_t', ylim=(1000, 0), levels=20, cmap='inferno', vmin=None, vmax=None, log_cbar=False):
    
    plot_list = []
    for variable in variable_dict.keys():
        if (vertical_dim in ds[variable].dims) and (variable != vertical_dim):
            ds_copy = ds.copy()
            ds_copy[variable] = ds_copy[variable].weighted(ds.dz).mean(dim='z_t')
            plot_list.append(line_plot(ds_copy, variable))
            
    out_panel = pn.Column()
    for plot in plot_list:
        out_panel+=plot
        
    return out_panel

def generate_line_plots(ds, variable_dict, ylim=None):
    
    plot_list = []
    for variable in variable_dict.keys():
        if variable not in ds.dims:
            plot_list.append(line_plot(ds, variable, ylim))
            
    out_panel = pn.Column()
    for plot in plot_list:
        out_panel+=plot
        
    return out_panel