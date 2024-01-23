import sys
import getopt
import damask
import numpy as np
import os
import matplotlib.pyplot as plt
import concurrent.futures
import glob

# Add phase and phase id information to vti files

    
def add_vti_info():
    def add_phaseID(filename):
        print(f"Working on {filename}")
        v = damask.VTK.load(filename)
        v = v.set('phase',p[material_ID],'phase')
        v = v.set('phaseID',pid[material_ID],'phaseID')
        v.save(filename)
        return None
    # Determine which .vti file is the geometry file
    vname = [_ for _ in glob.glob("*.vti") if 'inc' not in _]
    v = damask.VTK.load(vname[0])
    material_ID=v.get('material').flatten()
    # determine which .yaml file is the material.yaml file
    ma=None
    for each in [_ for _ in glob.glob("*.yaml")]:
        if damask.ConfigMaterial.load(each).is_complete:
            ma = damask.ConfigMaterial.load(each)
    phases = list(ma['phase'].keys())
    info = []

    for m in ma['material']:
        c = m['constituents'][0]
        phase = c['phase']
        info.append({'phase':   phase,
                     'phaseID': phases.index(phase),
                     'lattice': ma['phase'][phase]['lattice'],
                     'O':       c['O'],
                    })
    p   = np.array([d['phase'] for d in info])
    pid = np.array([d['phaseID'] for d in info])
    # The exported .vti files
    filelist = glob.glob('*_inc*.vti')
    # Parallelly add phaseid and phase to .vti files
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        r = executor.map(add_phaseID, filelist)
    # Collect files into a folder
    os.mkdir('vtis')
    for each in filelist:
        os.replace(each, "vtis/"+each)

# Get the argument from command line
def get_file_path():
    file_path = None
    argv = sys.argv[1:] 
    try:
        opts, args = getopt.getopt(argv, "f:", ["file_path ="])
    except:
        print("Error")
    
    for opt, arg in opts:
        if opt in['-f', '--file_path']:
            file_path=arg
    
    return file_path


# Add needed fields, assuming result file includes P and F.
def add_fields():
    print("Adding Cauchy stress tensor")
    try:
        result.add_stress_Cauchy()
    except:
        pass
    print("Adding right stretch tensor")
    try:
        result.add_stretch_tensor('F', 'U')
    except:
        pass
    print("Add spatial strain tensors")
    try:
        result.add_strain('F', 'U')
    except:
        pass
    print("Adding Mises equivalent strain")
    try:
        result.add_equivalent_Mises('epsilon_U^0.0(F)')
    except:
        pass
    print("Adding Mises equivalent stress")
    try:
        result.add_equivalent_Mises('sigma')
    except:
        pass
    print("Adding inverse pole color")
    try:
        result.add_IPF_color(np.array([1, 0, 0]))
    except:
        pass
    return None


# Plot all curves in a memory efficient way. Access increments one by one, and
# only store the phase and global averages. Reduce io and have some speed up


# Plot a true stress - true strain curve using sigma and 
# epsilon_U^0.0(F) in a specific load direction. Save plot
# in a separate file with identifiable name
# Load direction: 'x', 'y', 'z'
def plot_true_stress_strain():
    # If there are more than one phase, plot a line for each phase
    # as well as one for average of all phases. 
    data = result.get(['sigma', 'epsilon_U^0.0(F)'], flatten=False)
    # Initialize
    for load_direction in 'xyz':
        #print(f'Plotting true stress and true strain curve in {load_direction} axis')
        x_data = [[] for each in phases]
        y_data = [[] for each in phases]
        direction_index = 'xyz'.find(load_direction)
        # Plot macro stress-strain when there are more than one phase
        if multi_phase:
            # Get number of components in each phase
            x_data.append([])
            y_data.append([])
        for each_increment in data.values():
            macro_x = []
            macro_y = []
            for i in range(len(phases)):
                temp_x = each_increment['phase'][phases[i]]['mechanical']['epsilon_U^0.0(F)'][:, direction_index, direction_index]
                temp_y = each_increment['phase'][phases[i]]['mechanical']['sigma'][:, direction_index, direction_index]
                x_data[i].append(np.average(temp_x))
                y_data[i].append(np.average(temp_y))
                if multi_phase:
                    macro_x += list(temp_x)
                    macro_y += list(temp_y)
            if multi_phase:
                x_data[-1].append(np.average(macro_x))
                y_data[-1].append(np.average(macro_y))
    
        plt.figure(figsize=(12,8))
        for i in range(len(phases)):
            plt.plot([x*100 for x in x_data[i]], [y*1e-6 for y in y_data[i]], label=phases[i])
        if multi_phase:
            plt.plot([x*100 for x in x_data[-1]], [y*1e-6 for y in y_data[-1]], label='Macro')
        plt.legend()
        plt.xlabel('True strain (%)')
        plt.ylabel('True stress (MPa)')
        plt.title('True stress - true strain curve')
        fig_name = f'analysis_true_stress_strain_{load_direction}_{file_name}.png'
        plt.savefig(fig_name)
    # Memory management
    del x_data; del y_data; del macro_x; del macro_y; del temp_x; del temp_y
    return None

# Plot engineering stress-strain curve (P - F). The curve should
# look different compared to true stress - true strain, and shows
# the yielding point a bit more clearly
def plot_engineering_stress_strain():
    # If there are more than one phase, plot a line for each phase
    # as well as one for average of all phases. 
    data = result.get(['P', 'F'], flatten=False)
    # Initialize
    for load_direction in 'xyz':
        #print(f'Plotting engineering stress and strain curve in {load_direction} axis')
        x_data = [[] for each in phases]
        y_data = [[] for each in phases]
        direction_index = 'xyz'.find(load_direction)
        # Plot macro stress-strain when there are more than one phase
        if multi_phase:
            # Get number of components in each phase
            x_data.append([])
            y_data.append([])
        for each_increment in data.values():
            macro_x = []
            macro_y = []
            for i in range(len(phases)):
                temp_x = each_increment['phase'][phases[i]]['mechanical']['F'][:, direction_index, direction_index]
                temp_y = each_increment['phase'][phases[i]]['mechanical']['P'][:, direction_index, direction_index]
                x_data[i].append(np.average(temp_x))
                y_data[i].append(np.average(temp_y))
                if multi_phase:
                    macro_x += list(temp_x)
                    macro_y += list(temp_y)
            if multi_phase:
                x_data[-1].append(np.average(macro_x))
                y_data[-1].append(np.average(macro_y))
    
        plt.figure(figsize=(12,8))
        for i in range(len(phases)):
            plt.plot([(x-1)*100 for x in x_data[i]], [y*1e-6 for y in y_data[i]], label=phases[i])
        if multi_phase:
            plt.plot([(x-1)*100 for x in x_data[-1]], [y*1e-6 for y in y_data[-1]], label='Macro')
        plt.legend()
        plt.xlabel('Engineering strain (%)')
        plt.ylabel('Engineering stress (MPa)')
        plt.title('Engineering stress - strain curve')
        fig_name = f'analysis_engineering_stress_strain_{load_direction}_{file_name}.png'
        plt.savefig(fig_name)
    # Memory management
    del x_data; del y_data; del macro_x; del macro_y; del temp_x; del temp_y
    return None

def plot_dislocations():
    # Average dislocation densities
    data = result.get(['rho_mob', 'rho_dip', 'epsilon_U^0.0(F)'], flatten=False)
    # Prepare some plot lines
    for load_direction in 'xyz':
        x_data = [[] for each in phases]
        y_dip = [[] for each in phases]
        y_mob = [[] for each in phases]
        direction_index = 'xyz'.find(load_direction)
        # Average total dislocation densities
        for each_increment in data.values():
            for i in range(len(phases)):
                x_data[i].append(np.average(each_increment['phase'][phases[i]]['mechanical']['epsilon_U^0.0(F)'][:, direction_index, direction_index]))
                y_dip[i].append(np.average(np.sum(each_increment['phase'][phases[i]]['mechanical']['rho_dip'], axis=1)))
                y_mob[i].append(np.average(np.sum(each_increment['phase'][phases[i]]['mechanical']['rho_mob'], axis=1)))
        plt.figure(figsize=(12, 8))
        for i in range(len(phases)):
            plt.plot(x_data[i], y_dip[i], label=f"{phases[i]} dipole dislocation density")
            plt.plot(x_data[i], y_mob[i], label=f"{phases[i]} mobile dislocation density")
        plt.xlabel('True strain')
        plt.ylabel('Dislocation densities')
        plt.legend()
        plt.title('Average dislocation densities for all slip systems')
        fig_name = f'analysis_dislocation_densities_{load_direction}_{file_name}.png'
        plt.savefig(fig_name)
    # Memory management
    del x_data; del y_dip; del y_mob
    return None



if __name__ == '__main__':
    # Parse file name from file path
    path = get_file_path()
    # Remove the file extension, so we can use it later for
    # plot file names
    file_name = path.split("/")[-1][:-5]
    
    # Move to the folder containing result file and get the
    # result file there
    print(f"Processing result file {file_name} in {path[:-len(file_name)-5]}")
    os.chdir(path[:-len(file_name)-5])
    result = damask.Result(file_name+'.hdf5')
    # Get information from the result file object
    phases = result.phases
    multi_phase = len(phases) > 1
    increments = result.increments
    
    # Add fields and plot some datasets
    plot_engineering_stress_strain()
    add_fields()
    plot_true_stress_strain()
    plot_dislocations()
    
    # Export .vti files into the folder containing .hdf5 file
    ratio = 2       # Change the rate of vti files exported
    reduced=result.view(increments=result.increments[0::ratio])
    print(f"Exporting vtk")
    reduced.export_VTK(parallel=True)
    print(f"Adding phase ids to vtk")
    add_vti_info()
    
    
    print(f"Finished postprocessing")
