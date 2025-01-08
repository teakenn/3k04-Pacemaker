import tkinter as tk
from tkinter import messagebox
import serial.tools.list_ports
import csv
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import serialCom
from globalVars import defaultParams

# Setting default parameters for pacemaker
params = defaultParams()
 
# Global variables for entry fields and buttons
curr_user = None
entry_name = None
entry_password = None
btn_login = None
btn_register = None
lbl_device = None

# Finds current port
ports = list(serial.tools.list_ports.comports())
currPort = None
# To find port pacemaker is connected to:
for port in ports:
    print(port.description)

    if "JLink" in port.description: 
        currPort = port.device
        break

if currPort:
    print(f"Device is connected to: {currPort}")
else:
    print("Device not found.")

'''
# This is where the data structures that describe the egram data and plots exists
# and sample functions to simulate graphs based on random data
'''
 
# Collections of egram data will be conside#AA0000 objects
class EgramData:
 
    # Construct object
    def __init__(self):
        # Manage labelling x axis
        self.counter = 0
        self.timestamps = []
 
        # Labelling y axis
        self.voltages = []    
 
    # Setter. Take a datapoint and append to lists of past data
    def add_data(self, voltage):
 
        # Add timestamp and voltage to the lists
        self.timestamps.append(self.counter)
        self.voltages.append(voltage)
        self.counter+=1
       
        # Keep only the last 20 points
        if len(self.timestamps) > 20:
            self.timestamps = self.timestamps[-20:]
            self.voltages = self.voltages[-20:]
 
    # Getter for data
    def get_data(self):
        return self.timestamps, self.voltages

# Parent class of plots, each plot will have derived class in future assingments
class EgramPlotter:
    def __init__(self, title):
        # Initialize plot
        self.fig, self.ax = plt.subplots()
        self.title = title
        self.data = EgramData()
 
        # new code:
        self.ser = None  
        self.window = tk.Tk()
        self.window.title(self.title)
 
        # Embed the Matplotlib figure in the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
 
        # Add the exit button
        self.exit_button = tk.Button(self.window, text="Exit", command=self.close_window)
        self.exit_button.pack(side=tk.BOTTOM)
    
    # Closes egram plot window
    def close_window(self):
        """Close the graph window and properly close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial connection closed.")
        self.window.destroy()
 
    # This generates each frame of animation
    def animate(self, i):
        # Generate random voltage data
        # val = random.randrange(-10, 10, 1)
        # voltage = round(val, 2)
        with serial.Serial(currPort, baudrate=115200,timeout=1) as ser:
            voltage = serialCom.get_plotData(ser,params)
 
        # Add that data
        self.data.add_data(voltage)
 
        # Collect data for plotting every frame
        timestamps, voltages = self.data.get_data()
 
        # Draw the plot every time
        self.ax.clear()
        self.ax.plot(timestamps, voltages)
 
        # Format plot
        self.ax.set_title(self.title)
        self.ax.set_ylabel('Voltage(V)')
        plt.xticks(rotation=45)
 
 
    def start_animation(self, interval):
        anim = animation.FuncAnimation(self.fig, self.animate, interval=interval)
        self.window.mainloop()
    

def normalize(data, min_val=None, max_val=None):
        min_val = min_val if min_val is not None else min(data)
        max_val = max_val if max_val is not None else max(data)
        return [(v - min_val) / (max_val - min_val) for v in data] if max_val != min_val else [0.5 for _ in data]

 
# Shell derived class for atrium plot, will be used in future assingments
class AtriumPlotter(EgramPlotter):
    def __init__(self):
        # Initialize from the parent class
        super().__init__("Atrium Electrogram")

    def animate(self, i):
        with serial.Serial(currPort, baudrate=115200, timeout=1) as ser:
            voltages = serialCom.get_plotData(ser, params)

        if voltages is not None:
            voltage = voltages[0]  # Use unpacked[0] for atrium
            self.data.add_data(voltage)


        # Collect data for plotting every frame
        timestamps, voltages = self.data.get_data()

        # Draw the plot
        self.ax.clear()
        self.ax.plot(timestamps, voltages)

        # Format plot
        self.ax.set_title(self.title)
        self.ax.set_ylabel('Voltage(V)')
        self.ax.set_ylim(0, 1)  # Set static y-axis range
        plt.xticks(rotation=45)
 
 
# Shell derived class for ventricle plot, will be used in future assingments
class VentriclePlotter(EgramPlotter):
    def __init__(self):
        # Initialize from the parent class
        super().__init__("Ventricle Electrogram")

    def animate(self, i):
        with serial.Serial(currPort, baudrate=115200, timeout=1) as ser:
            voltages = serialCom.get_plotData(ser, params)
        
        if voltages is not None:
            voltage = voltages[1]  # Use unpacked[1] for ventricle
            self.data.add_data(voltage)
        
        # Collect data for plotting every frame
        timestamps, voltages = self.data.get_data()

        # Draw the plot
        self.ax.clear()
        self.ax.plot(timestamps, voltages)

        # Format plot
        self.ax.set_title(self.title)
        self.ax.set_ylabel('Voltage(V)')
        plt.xticks(rotation=45)
 
 
# Plot each graph
def plot_vent():
    ventricle_plotter = VentriclePlotter()
    ventricle_plotter.start_animation(100)
 
 
def plot_atrium():
    atrium_plotter = AtriumPlotter()
    atrium_plotter.start_animation(100)
 
'''
# This section contains functions that handle the logic for initializing and storing users
'''

def make_csvs():
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
    USER_FILE = os.path.join(FOLDER_PATH, 'users.csv')

    # Step 1: Create a new folder inside the directory to store CSV files
    output_folder = os.path.join(FOLDER_PATH, 'user_csvs')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Folder '{output_folder}' created.")
    else:
        print(f"Folder '{output_folder}' already exists.")

    # Step 2: Read each row of login info and create individual CSV files
    if os.path.exists(USER_FILE):
        with open(USER_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:  # Assuming each row contains [username, password]
                    username, password = row
                    user_file_path = os.path.join(output_folder, f"{username}.csv")

                    # Step 3: Create a CSV file for each username
                    with open(user_file_path, mode='w', newline='') as user_file:
                        writer = csv.writer(user_file)
                        # Write a header or any desired content for each user
                        writer.writerow(["ID", "Data"])
                        print(f"CSV file created for user: {username}")


# Load in users to check logins
def load_users():
    # Find path to CSV containing login info
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
    USER_FILE = os.path.join(FOLDER_PATH, 'users.csv')
 
    # Read each row of login info
    if os.path.exists(USER_FILE):
        with open(USER_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:  
 
                    # Add entry to dictionary
                    name, password = row
                    users_db[name] = password


# Locally save valid login info
def save_user(name, password):
 
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))  
    USER_FILE = os.path.join(FOLDER_PATH, 'users.csv')
 
    # Write all current logins to CSV
    with open(USER_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        for name, password in users_db.items():
            writer.writerow([name, password])
 
 
# Validation of user registration
def register_user():
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
    USER_FILE = os.path.join(FOLDER_PATH, 'users.csv')
 
    # Count the locally sto#AA0000 users
    userNum = 0
    if os.path.exists(USER_FILE):
        for row in open(USER_FILE):  
            userNum += 1
 
    # Pull user input
    name = entry_name.get()
    password = entry_password.get()
 
    # Check that both fields are filled
    if name and password:
        if userNum >= 10:
            messagebox.showerror("Error", "Too many users!")
        elif name in users_db:  
            messagebox.showerror("Error", "User already exists!")
        else:
            users_db[name] = password
            save_user(name, password)  
            messagebox.showinfo("Registration", "User registe#AA0000 successfully!")
    else:
        messagebox.showerror("Error", "Please fill out both fields.")
 
# Check user login with saved users
def login_user():
    # Pull user input
    name = entry_name.get()
    password = entry_password.get()

    # Validate login info
    if name in users_db and users_db[name] == password:
        messagebox.showinfo("Login", f"Welcome, {name}!")
        global curr_user
        curr_user = name
        make_csvs()
        mode_picker()
    else:
        messagebox.showerror("Error", "Incorrect username or password.")
 
'''
# This section contains the pacemaker discovery logic
'''
 
# Retrieve the unique device serial number
def get_serial(hwid):
    sections = hwid.split()
    for section in sections:
        if section.startswith("SER="):
            serial_number = section.split('=')[1]  # Get the value after "SER="
            return serial_number
 
# Check if there is a device connected and if so, return its info
def find_device():
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))  
    USER_FILE = os.path.join(FOLDER_PATH, 'devices.csv')
 
    # Create tuple of ports and their connected info
    ports = list(serial.tools.list_ports.comports())

    for port in ports:
        # Check if pacemaker is connected
         if "JLink" in port.description:
            return get_serial(port.hwid)  # Use hwid for hardware ID containing the serial number
    return None  
 
# Determine whether the device is new
def save_device():
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
    DEVICE_FILE = os.path.join(FOLDER_PATH, 'devices.csv')
    connected_device = find_device()
   
    if connected_device is None:
        print("No STM32 STLink device found.")
        return 0
 
    # Check if device is new
    if not os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, mode='w', newline='') as file:  # Create the file if it doesn't exist
            pass  # Just create an empty file
 
    with open(DEVICE_FILE, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if connected_device in row:
                print("Device already saved.")
                return 1
 
    # If not, write the device info to the CSV
    with open(DEVICE_FILE, mode='a', newline='') as file:  
        writer = csv.writer(file)
        writer.writerow([connected_device])
        print("Device saved.")
        messagebox.showinfo("Device", f"This device hasn't been connected yet!")
        return 2
 
'''
# This section contains the mode picker screen, and connected device logic
'''
 
# Determine the first device connected, will be referenced to tell if different
# device is approached
def get_first_device():
    device = save_device()
    # Check if there is a device connected or not
    if device != 0:
        # Indicate the first device has been identified
        global first_device_flag
        first_device_flag = True
        id = find_device()
        print(id)
        return id
 
# Handle alert mechanism when a different device is approached
def alert_user():
    # Set true flag, indicate user has been alerted
    global device_compare_flag
    device_compare_flag = True
    messagebox.showinfo("Warning: A different pacemaker is approached than was previously interrogated")
 
 
# Thread that updates connected device in background
def update_device_label():
    # Global var for first device, will be referenced for program runtime
    global first_device
    save_check = save_device()
    current_device = find_device()
   
    # Check if the device is not connected, new, or previously saved
    if save_check == 0:
        lbl_device.config(text="No device connected.")
    elif save_check == 1:
        lbl_device.config(text=f"Now communicating with device: \n{find_device()}")
       
        # if the first device hasn't been defined
        if first_device_flag == False:
            # Define first device
            first_device = get_first_device()
 
        # We only want the user to be alerted of different device once, so check
        # that there is a first device already, the current device is different,
        # and the user hasn't already been notified
        if (first_device_flag == True) and (current_device != first_device) and (device_compare_flag == False):
            alert_user()
 
        # When the first device is connected, get ready to flag different device
        if (first_device_flag == True) and (current_device == first_device):
            device_compare_flag = False
       
    else:
        lbl_device.config(text=f"Now communicating with device: \n{find_device()}")
 
        if first_device_flag == False:
            first_device = get_first_device()
       
        if (first_device_flag == True) and (current_device != first_device) and (device_compare_flag == False):
            alert_user()
 
        if (first_device_flag == True) and (current_device == first_device):
            device_compare_flag = False
       
    # Schedule the function to run recursively every 1000 ms
    root.after(1000, update_device_label)

def clear_window():
    for widget in root.winfo_children():
        if widget != lbl_device:  # Skip lbl_device
            widget.destroy()  # Destroy other widgets
        else:
            widget.grid_forget()  # Hide lbl_device, but don't destroy it

def logout_user():
    clear_window()  # Clear the current screen
    show_login_screen()  # Show the login screen again

def display_current_settings():
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))  
    SUBFOLDER = os.path.join(FOLDER_PATH, 'user_csvs')
 
    def get_user_csv_path(username):
        return os.path.join(SUBFOLDER, f"{username}.csv")
 
    # Get the path to the current user's CSV file
    PARAMETER_FILE = get_user_csv_path(curr_user)
 
    # Check if the CSV file exists
    if not os.path.exists(PARAMETER_FILE):
        messagebox.showerror("Error", "No saved settings found for the current user!")
        return
 
    try:
        # Read the last row from the CSV file
        with open(PARAMETER_FILE, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)  # Read all rows into a list
            if not rows:  # Check if the file is empty
                messagebox.showerror("Error", "No settings found in the file!")
                return
            last_row = rows[-1]  # Get the most recent settings
 
        # Display the settings in a popup
        settings_display = "\n".join([f"{key}: {value}" for key, value in enumerate(last_row)])
        messagebox.showinfo("Current Settings", f"Most Recent Settings:\n\n{settings_display}")
 
    except Exception as e:
        messagebox.showerror("Error", f"Could not read settings: {str(e)}")        
# Call this to create the mode selector window
def mode_picker():
    clear_window()
    global lbl_device
    root.title("Select mode")
    root.geometry("450x450")  # Set appropriate window size

    # Adjust grid configuration to remove empty middle space
    root.grid_columnconfigure(0, weight=1)  # Left margin
    root.grid_columnconfigure(1, weight=1)  # VOO and VVI buttons
    root.grid_columnconfigure(2, weight=1)  # AOO and AAI buttons
    root.grid_columnconfigure(3, weight=1)  # Right margin

    root.grid_rowconfigure(0, weight=1)  # Top margin row
    root.grid_rowconfigure(1, weight=1)  # Title row
    root.grid_rowconfigure(2, weight=1)  # Buttons row 1
    root.grid_rowconfigure(3, weight=1)  # Buttons row 2
    root.grid_rowconfigure(4, weight=1)  # Buttons row 3
    root.grid_rowconfigure(5, weight=1)  # Buttons row 4
    root.grid_rowconfigure(6, weight=1)  # Egram row
    root.grid_rowconfigure(7, weight=1)  # Bottom margin row

    # Device label at the top with darker #AA0000 text
    lbl_device = tk.Label(root, text="No device connected.", font=("Helvetica", 10, "bold"), fg="#AA0000")
    lbl_device.grid(row=0, column=0, columnspan=4, pady=(8, 10))

    # Title label
    lbl_title = tk.Label(root, text="Select Pacing Mode", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=1, column=0, columnspan=4, pady=(10, 20))

    # VOO button (left side)
    btn_voo = tk.Button(root, text="VOO", command=open_voo_pacing_settings, width=12, height=2)
    btn_voo.grid(row=2, column=1, padx=10, pady=10)

    # AOO button (right side)
    btn_aoo = tk.Button(root, text="AOO", command=open_aoo_pacing_settings, width=12, height=2)
    btn_aoo.grid(row=2, column=2, padx=10, pady=10)

    # VVI button (left side)
    btn_vvi = tk.Button(root, text="VVI", command=open_vvi_pacing_settings, width=12, height=2)
    btn_vvi.grid(row=3, column=1, padx=10, pady=10)

    # AAI button (right side)
    btn_aai = tk.Button(root, text="AAI", command=open_aai_pacing_settings, width=12, height=2)
    btn_aai.grid(row=3, column=2, padx=10, pady=10)

    # VOOR button (left side)
    btn_voor = tk.Button(root, text="VOOR", command=open_voor_pacing_settings, width=12, height=2)
    btn_voor.grid(row=4, column=1, padx=10, pady=10)

    # AOOR button (right side)
    btn_aoor = tk.Button(root, text="AOOR", command=open_aoor_pacing_settings, width=12, height=2)
    btn_aoor.grid(row=4, column=2, padx=10, pady=10)

    # VVIR button (left side)
    btn_vvir = tk.Button(root, text="VVIR", command=open_vvir_pacing_settings, width=12, height=2)
    btn_vvir.grid(row=5, column=1, padx=10, pady=10)

    # AAIR button (right side)
    btn_aair = tk.Button(root, text="AAIR", command=open_aair_pacing_settings, width=12, height=2)
    btn_aair.grid(row=5, column=2, padx=10, pady=10)

    # Egram buttons placed in a single row at the bottom
    btn_vent_egram = tk.Button(root, text="Ventricle Egram", command=plot_vent, width=12, height=2)
    btn_vent_egram.grid(row=6, column=1, padx=10, pady=10)

    btn_atrial_egram = tk.Button(root, text="Atrium Egram", command=plot_atrium, width=12, height=2)
    btn_atrial_egram.grid(row=6, column=2, padx=10, pady=10)

    # Logout button
    btn_logout = tk.Button(root, text="Logout", command=logout_user, bg="#AA0000", fg="white", width=10, height=2)
    btn_logout.grid(row=7, column=0, columnspan=4, pady=(20, 20))  # Cente#AA0000 below the mode selection buttons

    # User indication
    lbl_username = tk.Label(root, text=f"----  {curr_user} is logged in  ----", font=("Helvetica", 10, "bold"), fg="green")
    lbl_username.grid(row=8, column=0, columnspan=4, pady=(0, 20))
 
    # Current settings button
    btn_settings = tk.Button(root, text="Current Settings", command=display_current_settings, bg="#E49B0F", fg="white", width=15, height=2)
    btn_settings.grid(row=7, column=1, columnspan=4, padx=(0,230), pady=(20, 20))  # Cente#AA0000 below the mode selection buttons

    # Run this function recursively, update the connected device at interval
    update_device_label()

'''
# This section handles the logic of storing the parameters to a CSV
'''
 
# # Initialize CSV to store data
# def initialize_csv_file():
#     FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))  
#     PARAMETER_FILE = os.path.join(FOLDER_PATH, 'pacing_parameters.csv')
#     with open(PARAMETER_FILE, mode='w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(['Time', 'VOO', 'AOO', 'VVI', 'AAI', 'Values'])        
 

def save_settings(mode, params):
    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))  
    SUBFOLDER = os.path.join(FOLDER_PATH, 'user_csvs')

    def get_user_csv_path(username):
        return os.path.join(SUBFOLDER, f"{username}.csv")
    
    PARAMETER_FILE = get_user_csv_path(curr_user)
 
    # Open the CSV file in append mode
    with open(PARAMETER_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Check for mode and write appropriate data to CSV
        if mode == 'VOO':
            writer.writerow([0, params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["vent_amp"], params["vent_pw"]])
        elif mode == 'AOO':
            writer.writerow([0, params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["atr_amp"], params["atr_pw"]])
        elif mode == 'VVI':
            writer.writerow([0, params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["vent_amp"], params["vent_pw"], params["vent_sens"], params["vrp"]])
        elif mode == 'AAI':
            writer.writerow([0, params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["atr_amp"], params["atr_pw"], params["atr_sens"], params["arp"], params["pvarp"]])
        elif mode == 'VOOR':
            writer.writerow([0, params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["vent_amp"], params["vent_pw"], params["msr"], params["act_thresh"], params["reaction_time"], params["response_fact"], params["recovery_time"]])  
        elif mode == 'AOOR':
            writer.writerow([0, params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["atr_amp"], params["atr_pw"], params["msr"], params["act_thresh"], params["reaction_time"], params["response_fact"], params["recovery_time"]])  
        elif mode == 'VVIR':
            writer.writerow([0,params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["vent_amp"], params["vent_pw"], params["vent_sens"], params["vrp"], params["msr"], params["act_thresh"], params["reaction_time"], params["response_fact"], params["recovery_time"]])  
        elif mode == 'AAIR':
            writer.writerow([0, params["mode"], params["rate_adapt"], params["lrl"], params["url"], params["atr_amp"], params["atr_pw"], params["atr_sens"], params["arp"], params["pvarp"], params["msr"], params["act_thresh"], params["reaction_time"], params["response_fact"], params["recovery_time"]])  

'''
# Create windows for user input for each setting
'''
 
# Call this to open the VOO settings to input
def open_voo_pacing_settings():
    clear_window()
    root.title("VOO Pacing Settings")
    root.geometry("400x300")

    # Format the page grid
    root.grid_columnconfigure(0, weight=1)  # Empty space on left
    root.grid_columnconfigure(1, weight=0)  # Main elements
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  # Empty space on right
    root.grid_rowconfigure(0, weight=1)  # Space above elements
    root.grid_rowconfigure(7, weight=1)  # Space below elements
 
    # Put title
    lbl_title = tk.Label(root, text="VOO Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    # Ventricle Amplitude
    lbl_va = tk.Label(root, text="Ventricular Amplitude:")
    lbl_va.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_va = tk.Entry(root)
    entry_va.grid(row=3, column=2, padx=10, pady=5)
 
    # Ventricle Pulse Width
    lbl_pw = tk.Label(root, text="Ventricular Pulse Width:")
    lbl_pw.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=4, column=2, padx=10, pady=5)
 
    # Placeholder for submission status message
    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=5, column=1, columnspan=2, pady=5)
 
    # Input validation for submission of parameters
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        # Handle the cases that the entries aren't numbers and not all filled
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            va = float(entry_va.get())
            va = round(va, 1)
            if (va>5 or va<0):
                raise ValueError("Amplitude must not be between 0-5.0")
            pw = int(entry_pw.get())
            pw = round(pw)
            if (pw < 1 or pw > 30):
                raise ValueError("Pulse Width must be between 1-30")
           
        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        # Handle case when there's no board
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return
 
        # updating new pacing settings
        params["mode"] = 2
        params["rate_adapt"] = 0
        params["lrl"] = lrl
        params["url"] = url
        params["vent_amp"] = va
        params["vent_pw"] = pw

        # Save settings if all fields are numbers and a device is connected
        save_settings('VOO', params)
        lbl_status.config(text="Settings have been saved!", fg="green")
        
        # sending parameters to pacemaker
        serialCom.send_parameters(params,currPort)
 
        # After 3 seconds clear the message
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=6, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=8, column=1, columnspan=2, pady=(10, 20))

 
# Call this to open the AOO settings to input
def open_aoo_pacing_settings():
    clear_window()
    root.title("AOO Pacing Settings")
    root.geometry("400x300")
 
    # Layout
    root.grid_columnconfigure(0, weight=1)  
    root.grid_columnconfigure(1, weight=0)  
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(6, weight=1)  
 
    lbl_title = tk.Label(root, text="AOO Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    # Atrial Amplitude
    lbl_aa = tk.Label(root, text="Atrial Amplitude:")
    lbl_aa.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_aa = tk.Entry(root)
    entry_aa.grid(row=3, column=2, padx=10, pady=5)
 
    # Atrial Pulse Width
    lbl_pw = tk.Label(root, text="Atrial Pulse Width:")
    lbl_pw.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=4, column=2, padx=10, pady=5)

    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=5, column=1, columnspan=2, pady=5)
 
    # Handle submission validation, refer to VOO function of same name
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            aa = float(entry_aa.get())
            aa = round(aa, 1)
            if (aa>5 or aa<0):
                raise ValueError("Amplitude must not be between 0-5.0")
            pw = int(entry_pw.get())
            pw = round(pw)
            if (pw < 1 or pw > 30):
                raise ValueError("Pulse Width must be between 1-30")
           
        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return

        # Updating new settings
        params["mode"] = 1
        params["rate_adapt"] = 0
        params["lrl"] = lrl
        params["url"] = url
        params["atr_amp"] = aa
        params["atr_pw"] = pw
        
        save_settings('AOO',params)
        # Sending parameters to pacemaker
        serialCom.send_parameters(params,currPort)

        lbl_status.config(text="Settings have been saved!", fg="green")
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=6, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=8, column=1, columnspan=2, pady=(10, 20))

# For VVI input
def open_vvi_pacing_settings():
    clear_window()
    root.title("VVI Pacing Settings")
    root.geometry("400x400")
 
    root.grid_columnconfigure(0, weight=1)  
    root.grid_columnconfigure(1, weight=0)  
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(9, weight=1)  
 
    lbl_title = tk.Label(root, text="VVI Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    # Ventricular Amplitude
    lbl_va = tk.Label(root, text="Ventricular Amplitude:")
    lbl_va.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_va = tk.Entry(root)
    entry_va.grid(row=3, column=2, padx=10, pady=5)
 
    # Ventricular Pulse Width
    lbl_pw = tk.Label(root, text="Ventricular Pulse Width:")
    lbl_pw.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=4, column=2, padx=10, pady=5)
 
    # Ventricular Sensitivity
    lbl_vs = tk.Label(root, text="Ventricular Sensitivity:")
    lbl_vs.grid(row=5, column=1, sticky="e", padx=10, pady=5)
    entry_vs = tk.Entry(root)
    entry_vs.grid(row=5, column=2, padx=10, pady=5)
 
    # VRP
    lbl_vrp = tk.Label(root, text="VRP:")
    lbl_vrp.grid(row=6, column=1, sticky="e", padx=10, pady=5)
    entry_vrp = tk.Entry(root)
    entry_vrp.grid(row=6, column=2, padx=10, pady=5)  
 
    # Label to indicate settings have been saved (initially empty)
    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=7, column=1, columnspan=2, pady=5)
 
    # Handle submission validation, refer to VOO function of same name
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            va = float(entry_va.get())
            va = round(va, 1)
            if (va>5 or va<0):
                raise ValueError("Amplitude must not be between 0-5.0")
            pw = int(entry_pw.get())
            pw = round(pw)
            if (pw < 1 or pw > 30):
                raise ValueError("Pulse Width must be between 1-30")
            vsens = int(entry_vs.get())
            if (vsens > 5 or vsens < 0):
                raise ValueError("Sensitivity must be between 0-5.0")
            vrp = int(entry_vrp.get())
            
        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return

        params["mode"] = 4
        params["rate_adapt"] = 0
        params["lrl"] = lrl
        params["url"] = url
        params["vent_amp"] = va
        params["vent_pw"] = pw
        params["vent_sens"] = vsens
        params["vrp"] = vrp

        save_settings('VVI', params)
        serialCom.send_parameters(params,currPort)

        lbl_status.config(text="Settings have been saved!", fg="green")
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=8, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=11, column=1, columnspan=2, pady=(10, 20))

# For AAI input
def open_aai_pacing_settings():
    clear_window()
    root.title("AAI Pacing Settings")
    root.geometry("500x500")
 
    root.grid_columnconfigure(0, weight=1)  
    root.grid_columnconfigure(1, weight=0)  
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(9, weight=1)
 
    lbl_title = tk.Label(root, text="AAI Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    # Atrial Amplitude
    lbl_aa = tk.Label(root, text="Atrial Amplitude:")
    lbl_aa.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_aa = tk.Entry(root)
    entry_aa.grid(row=3, column=2, padx=10, pady=5)
 
    # Atrial Pulse Width
    lbl_pw = tk.Label(root, text="Atrial Pulse Width:")
    lbl_pw.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=4, column=2, padx=10, pady=5)
 
    # Atrial Sensitivity
    lbl_as = tk.Label(root, text="Atrial Sensitivity:")
    lbl_as.grid(row=5, column=1, sticky="e", padx=10, pady=5)
    entry_as = tk.Entry(root)
    entry_as.grid(row=5, column=2, padx=10, pady=5)
 
    # ARP
    lbl_arp = tk.Label(root, text="ARP:")
    lbl_arp.grid(row=6, column=1, sticky="e", padx=10, pady=5)
    entry_arp = tk.Entry(root)
    entry_arp.grid(row=6, column=2, padx=10, pady=5)
 
    # PVARP
    lbl_pvarp = tk.Label(root, text="PVARP:")
    lbl_pvarp.grid(row=7, column=1, sticky="e", padx=10, pady=5)
    entry_pvarp = tk.Entry(root)
    entry_pvarp.grid(row=7, column=2, padx=10, pady=5)
 
    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=8, column=1, columnspan=2, pady=5)
 
    # Handle submission validation, refer to VOO function of same name
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            aa = float(entry_aa.get())
            aa = round(aa, 1)
            if (aa>5 or aa<0):
                raise ValueError("Amplitude must not be between 0-5.0")
            pw = int(entry_pw.get())
            pw = round(pw)
            if (pw < 1 or pw > 30):
                raise ValueError("Pulse Width must be between 1-30")
            asens = int(entry_as.get())
            if (asens > 5 or asens < 0):
                raise ValueError("Sensitivity must be between 0-5.0")
            arp = int(entry_arp.get())
            pvarp = int(entry_pvarp.get())

        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return  
 
        params["mode"] = 3
        params["rate_adapt"] = 0
        params["lrl"] = lrl
        params["url"] = url
        params["atr_amp"] = aa
        params["atr_pw"] = pw
        params["atr_sens"] = asens
        params["arp"] = arp
        params["pvarp"] = pvarp

        save_settings('AAI',params)
        serialCom.send_parameters(params,currPort)

        lbl_status.config(text="Settings have been saved!", fg="green")
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=9, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=11, column=1, columnspan=2, pady=(10, 20))

 
#NEW ASSIGNMENT 2 PARAMETERS

# Call this to open the VOO settings to input
def open_voor_pacing_settings():
    clear_window()
    root.title("VOOR Pacing Settings")
    root.geometry("400x600")
 
    # Format the page grid
    root.grid_columnconfigure(0, weight=1)  # Empty space on left
    root.grid_columnconfigure(1, weight=0)  # Main elements
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  # Empty space on right
    root.grid_rowconfigure(0, weight=1)  # Space above elements
    root.grid_rowconfigure(7, weight=1)  # Space below elements
 
    # Put title
    lbl_title = tk.Label(root, text="VOOR Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    # max sensor rate
    lbl_msr = tk.Label(root, text="Maximum Sensor Rate:")
    lbl_msr.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_msr = tk.Entry(root)
    entry_msr.grid(row=3, column=2, padx=10, pady=5)
 
    #activity threshold
    lbl_at = tk.Label(root, text="Activity Threshold:")
    lbl_at.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_at = tk.Entry(root)
    entry_at.grid(row=4, column=2, padx=10, pady=5)
 
    #reaction time
    lbl_rt = tk.Label(root, text="Reaction Time")
    lbl_rt.grid(row=5, column=1, sticky="e", padx=10, pady=5)
    entry_rt = tk.Entry(root)
    entry_rt.grid(row=5, column=2, padx=10, pady=5)
 
    #response factor
    lbl_rf = tk.Label(root, text="Response Factor")
    lbl_rf.grid(row=6, column=1, sticky="e", padx=10, pady=5)
    entry_rf = tk.Entry(root)
    entry_rf.grid(row=6, column=2, padx=10, pady=5)
 
    #recovery time
    lbl_rct = tk.Label(root, text="Recovery Time")
    lbl_rct.grid(row=7, column=1, sticky="e", padx=10, pady=5)
    entry_rct = tk.Entry(root)
    entry_rct.grid(row=7, column=2, padx=10, pady=5)
 
    # Ventricle Amplitude
    lbl_va = tk.Label(root, text="Ventricular Amplitude:")
    lbl_va.grid(row=8, column=1, sticky="e", padx=10, pady=5)
    entry_va = tk.Entry(root)
    entry_va.grid(row=8, column=2, padx=10, pady=5)
 
    # Ventricle Pulse Width
    lbl_pw = tk.Label(root, text="Ventricular Pulse Width:")
    lbl_pw.grid(row=9, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=9, column=2, padx=10, pady=5)
 
    # Placeholder for submission status message
    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=10, column=1, columnspan=2, pady=5)
 
    # Input validation for submission of parameters
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        # Handle the cases that the entries aren't numbers and not all filled
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            msr = int(entry_msr.get())
            at = float(entry_at.get())
            rt = int(entry_rt.get())
            rf = int(entry_rf.get())
            rct = int(entry_rct.get())
            va = float(entry_va.get())
            va = round(va, 1)
            if (va>5 or va<0):
                raise ValueError("Amplitude must not be between 0-5.0")
            pw = int(entry_pw.get())
            pw = round(pw)
            if (pw < 1 or pw > 30):
                raise ValueError("Pulse Width must be between 1-30")
           
        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        # Handle case when there's no board
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return

        params["mode"] = 2
        params["rate_adapt"] = 1
        params["lrl"] = lrl
        params["url"] = url
        params["vent_amp"] = va
        params["vent_pw"] = pw
        params["msr"] = msr
        params["act_thresh"] = at
        params["reaction_time"] = rt
        params["response_fact"] = rf
        params["recovery_time"] = rct
        # Save settings if all fields are numbers and a device is connected
        save_settings('VOOR', params)
        serialCom.send_parameters(params,currPort)
        lbl_status.config(text="Settings have been saved!", fg="green")
        # After 3 seconds clear the message
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=11, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=13, column=1, columnspan=2, pady=(10, 20))
 
# Call this to open the AOO settings to input
def open_aoor_pacing_settings():
    clear_window()
    root.title("AOOR Pacing Settings")
    root.geometry("400x500")
 
    # Layout
    root.grid_columnconfigure(0, weight=1)  
    root.grid_columnconfigure(1, weight=0)  
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(6, weight=1)  
 
    lbl_title = tk.Label(root, text="AOOR Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    # max sensor rate
    lbl_msr = tk.Label(root, text="Maximum Sensor Rate:")
    lbl_msr.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_msr = tk.Entry(root)
    entry_msr.grid(row=3, column=2, padx=10, pady=5)
 
    #activity threshold
    lbl_at = tk.Label(root, text="Activity Threshold:")
    lbl_at.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_at = tk.Entry(root)
    entry_at.grid(row=4, column=2, padx=10, pady=5)
 
    #reaction time
    lbl_rt = tk.Label(root, text="Reaction Time")
    lbl_rt.grid(row=5, column=1, sticky="e", padx=10, pady=5)
    entry_rt = tk.Entry(root)
    entry_rt.grid(row=5, column=2, padx=10, pady=5)
 
    #response factor
    lbl_rf = tk.Label(root, text="Response Factor")
    lbl_rf.grid(row=6, column=1, sticky="e", padx=10, pady=5)
    entry_rf = tk.Entry(root)
    entry_rf.grid(row=6, column=2, padx=10, pady=5)
 
    #recovery time
    lbl_rct = tk.Label(root, text="Recovery Time")
    lbl_rct.grid(row=7, column=1, sticky="e", padx=10, pady=5)
    entry_rct = tk.Entry(root)
    entry_rct.grid(row=7, column=2, padx=10, pady=5)
 
    # Atrial Amplitude
    lbl_aa = tk.Label(root, text="Atrial Amplitude:")
    lbl_aa.grid(row=8, column=1, sticky="e", padx=10, pady=5)
    entry_aa = tk.Entry(root)
    entry_aa.grid(row=8, column=2, padx=10, pady=5)
 
    # Atrial Pulse Width
    lbl_pw = tk.Label(root, text="Atrial Pulse Width:")
    lbl_pw.grid(row=9, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=9, column=2, padx=10, pady=5)
 
    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=10, column=1, columnspan=2, pady=5)
 
    # Handle submission validation, refer to VOO function of same name
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            msr = int(entry_msr.get())
            at = float(entry_at.get())
            rt = int(entry_rt.get())
            rf = int(entry_rf.get())
            rct = int(entry_rct.get())
            aa = float(entry_aa.get())
            aa = round(aa, 1)
            if (aa>5 or aa<0):
                raise ValueError("Amplitude must not be between 0-5.0")
            pw = int(entry_pw.get())
            pw = round(pw)
            if (pw < 1 or pw > 30):
                raise ValueError("Pulse Width must be between 1-30")
           
        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return
        
        params["mode"] = 1
        params["rate_adapt"] = 1
        params["lrl"] = lrl
        params["url"] = url
        params["atr_amp"] = aa
        params["atr_pw"] = pw
        params["msr"] = msr
        params["act_thresh"] = at
        params["reaction_time"] = rt
        params["response_fact"] = rf
        params["recovery_time"] = rct
 
        save_settings('AOOR', params)
        serialCom.send_parameters(params,currPort)

        lbl_status.config(text="Settings have been saved!", fg="green")
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=11, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=13, column=1, columnspan=2, pady=(10, 20))

# For VVIR pacing
def open_vvir_pacing_settings():
    clear_window()
    root.title("VVIR Pacing Settings")
    root.geometry("400x550")
 
    root.grid_columnconfigure(0, weight=1)  
    root.grid_columnconfigure(1, weight=0)  
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(9, weight=1)  
 
    lbl_title = tk.Label(root, text="VVIR Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    # max sensor rate
    lbl_msr = tk.Label(root, text="Maximum Sensor Rate:")
    lbl_msr.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_msr = tk.Entry(root)
    entry_msr.grid(row=3, column=2, padx=10, pady=5)
 
    #activity threshold
    lbl_at = tk.Label(root, text="Activity Threshold:")
    lbl_at.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_at = tk.Entry(root)
    entry_at.grid(row=4, column=2, padx=10, pady=5)
 
    #reaction time
    lbl_rt = tk.Label(root, text="Reaction Time")
    lbl_rt.grid(row=5, column=1, sticky="e", padx=10, pady=5)
    entry_rt = tk.Entry(root)
    entry_rt.grid(row=5, column=2, padx=10, pady=5)
 
    #response factor
    lbl_rf = tk.Label(root, text="Response Factor")
    lbl_rf.grid(row=6, column=1, sticky="e", padx=10, pady=5)
    entry_rf = tk.Entry(root)
    entry_rf.grid(row=6, column=2, padx=10, pady=5)
 
    #recovery time
    lbl_rct = tk.Label(root, text="Recovery Time")
    lbl_rct.grid(row=7, column=1, sticky="e", padx=10, pady=5)
    entry_rct = tk.Entry(root)
    entry_rct.grid(row=7, column=2, padx=10, pady=5)
 
    # Ventricular Amplitude
    lbl_va = tk.Label(root, text="Ventricular Amplitude:")
    lbl_va.grid(row=8, column=1, sticky="e", padx=10, pady=5)
    entry_va = tk.Entry(root)
    entry_va.grid(row=8, column=2, padx=10, pady=5)
 
    # Ventricular Pulse Width
    lbl_pw = tk.Label(root, text="Ventricular Pulse Width:")
    lbl_pw.grid(row=9, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=9, column=2, padx=10, pady=5)
 
    # Ventricular Sensitivity
    lbl_vs = tk.Label(root, text="Ventricular Sensitivity:")
    lbl_vs.grid(row=10, column=1, sticky="e", padx=10, pady=5)
    entry_vs = tk.Entry(root)
    entry_vs.grid(row=10, column=2, padx=10, pady=5)
 
    # VRP
    lbl_vrp = tk.Label(root, text="VRP:")
    lbl_vrp.grid(row=11, column=1, sticky="e", padx=10, pady=5)
    entry_vrp = tk.Entry(root)
    entry_vrp.grid(row=11, column=2, padx=10, pady=5)
 
    # Label to indicate settings have been saved (initially empty)
    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=12, column=1, columnspan=2, pady=5)
 
    # Handle submission validation, refer to VOO function of same name
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            msr = int(entry_msr.get())
            at = float(entry_at.get())
            rt = int(entry_rt.get())
            rf = int(entry_rf.get())
            rct = int(entry_rct.get())
            va = float(entry_va.get())
            va = round(va, 1)
            if (va>5 or va<0):
                raise ValueError("Amplitude must not be between 0-5.0")
            pw = int(entry_pw.get())
            pw = round(pw)
            if (pw < 1 or pw > 30):
                raise ValueError("Pulse Width must be between 1-30")
            vsens = int(entry_vs.get())
            if (vsens > 5 or vsens < 0):
                raise ValueError("Sensitivity must be between 0-5.0")
            vrp = int(entry_vrp.get())

        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return
        
        params["mode"] = 4
        params["rate_adapt"] = 1
        params["lrl"] = lrl
        params["url"] = url
        params["vent_amp"] = va
        params["vent_pw"] = pw
        params["vent_sens"] = vsens
        params["vrp"] = vrp
        params["msr"] = msr
        params["act_thresh"] = at
        params["reaction_time"] = rt
        params["response_fact"] = rf
        params["recovery_time"] = rct
 
        save_settings('VVIR', params)
        serialCom.send_parameters(params,currPort)
        lbl_status.config(text="Settings have been saved!", fg="green")
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=13, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=15, column=1, columnspan=2, pady=(10, 20))

# For AAIR parameters
def open_aair_pacing_settings():
    clear_window()
    root.title("AAIR Pacing Settings")
    root.geometry("400x550")
 
    root.grid_columnconfigure(0, weight=1)  
    root.grid_columnconfigure(1, weight=0)  
    root.grid_columnconfigure(2, weight=0)  
    root.grid_columnconfigure(3, weight=1)  
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(9, weight=1)
 
    lbl_title = tk.Label(root, text="AAIR Pacing Settings", font=("Helvetica", 14, "bold"))
    lbl_title.grid(row=0, column=1, columnspan=2, pady=(10, 20))
 
    # Lower Rate Limit (LRL)
    lbl_lrl = tk.Label(root, text="Lower Rate Limit (LRL):")
    lbl_lrl.grid(row=1, column=1, sticky="e", padx=10, pady=5)
    entry_lrl = tk.Entry(root)
    entry_lrl.grid(row=1, column=2, padx=10, pady=5)
 
    # Upper Rate Limit (URL)
    lbl_url = tk.Label(root, text="Upper Rate Limit (URL):")
    lbl_url.grid(row=2, column=1, sticky="e", padx=10, pady=5)
    entry_url = tk.Entry(root)
    entry_url.grid(row=2, column=2, padx=10, pady=5)
 
    #max sensor rate
    lbl_msr = tk.Label(root, text="Maximum Sensor Rate:")
    lbl_msr.grid(row=3, column=1, sticky="e", padx=10, pady=5)
    entry_msr = tk.Entry(root)
    entry_msr.grid(row=3, column=2, padx=10, pady=5)
 
    #activity threshold
    lbl_at = tk.Label(root, text="Activity Threshold:")
    lbl_at.grid(row=4, column=1, sticky="e", padx=10, pady=5)
    entry_at = tk.Entry(root)
    entry_at.grid(row=4, column=2, padx=10, pady=5)
 
    #reaction time
    lbl_rt = tk.Label(root, text="Reaction Time")
    lbl_rt.grid(row=5, column=1, sticky="e", padx=10, pady=5)
    entry_rt = tk.Entry(root)
    entry_rt.grid(row=5, column=2, padx=10, pady=5)
 
    #response factor
    lbl_rf = tk.Label(root, text="Response Factor")
    lbl_rf.grid(row=6, column=1, sticky="e", padx=10, pady=5)
    entry_rf = tk.Entry(root)
    entry_rf.grid(row=6, column=2, padx=10, pady=5)
 
    #recovery time
    lbl_rct = tk.Label(root, text="Recovery Time")
    lbl_rct.grid(row=7, column=1, sticky="e", padx=10, pady=5)
    entry_rct = tk.Entry(root)
    entry_rct.grid(row=7, column=2, padx=10, pady=5)
 
    # Atrial Amplitude
    lbl_aa = tk.Label(root, text="Atrial Amplitude:")
    lbl_aa.grid(row=8, column=1, sticky="e", padx=10, pady=5)
    entry_aa = tk.Entry(root)
    entry_aa.grid(row=8, column=2, padx=10, pady=5)
 
    # Atrial Pulse Width
    lbl_pw = tk.Label(root, text="Atrial Pulse Width:")
    lbl_pw.grid(row=9, column=1, sticky="e", padx=10, pady=5)
    entry_pw = tk.Entry(root)
    entry_pw.grid(row=9, column=2, padx=10, pady=5)
 
    # Atrial Sensitivity
    lbl_as = tk.Label(root, text="Atrial Sensitivity:")
    lbl_as.grid(row=10, column=1, sticky="e", padx=10, pady=5)
    entry_as = tk.Entry(root)
    entry_as.grid(row=10, column=2, padx=10, pady=5)
 
    # ARP
    lbl_arp = tk.Label(root, text="ARP:")
    lbl_arp.grid(row=11, column=1, sticky="e", padx=10, pady=5)
    entry_arp = tk.Entry(root)
    entry_arp.grid(row=11, column=2, padx=10, pady=5)
 
    # PVARP
    lbl_pvarp = tk.Label(root, text="PVARP:")
    lbl_pvarp.grid(row=12, column=1, sticky="e", padx=10, pady=5)
    entry_pvarp = tk.Entry(root)
    entry_pvarp.grid(row=12, column=2, padx=10, pady=5)
 
    lbl_status = tk.Label(root, text="", fg="green")
    lbl_status.grid(row=13, column=1, columnspan=2, pady=5)
 
    # Handle submission validation, refer to VOO function of same name
    def handle_submit():
        current_device = find_device()
        params = defaultParams()
 
        try:
            lrl = int(entry_lrl.get())
            url = int(entry_url.get())
            msr = int(entry_msr.get())
            at = float(entry_at.get())
            rt = int(entry_rt.get())
            rf = int(entry_rf.get())
            rct = int(entry_rct.get())
            aa = float(entry_aa.get())
            pw = int(entry_pw.get())
            asens = int(entry_as.get())
            arp = int(entry_arp.get())
            pvarp = int(entry_pvarp.get())

        except ValueError:
            lbl_status.config(text="Please enter all fields as valid numbers!", fg="#AA0000")
            return
 
        if current_device is None:
            lbl_status.config(text="Please connect a board!", fg="#AA0000")
            return  
 
        params["mode"] = 3
        params["rate_adapt"] = 1
        params["lrl"] = lrl
        params["url"] = url
        params["atr_amp"] = aa
        params["atr_pw"] = pw
        params["atr_sens"] = asens
        params["arp"] = arp
        params["pvarp"] = pvarp
        params["msr"] = msr
        params["act_thresh"] = at
        params["reaction_time"] = rt
        params["response_fact"] = rf
        params["recovery_time"] = rct

        save_settings('AAIR', params)
        serialCom.send_parameters(params,currPort)
        lbl_status.config(text="Settings have been saved!", fg="green")
 
        root.after(3000, lambda: lbl_status.config(text=""))
 
    # Submit button
    btn_submit = tk.Button(root, text="Submit", command=handle_submit)
    btn_submit.grid(row=14, column=1, columnspan=2, pady=10)

    # Back button to go to the mode_picker screen
    btn_back = tk.Button(root, text="Back", command=mode_picker, bg="#E49B0F", fg="white", width=10, height=1)
    btn_back.grid(row=16, column=1, columnspan=2, pady=(10, 20))

 
'''
# This section handles events that are bound to keys
'''
 
def on_login_enter_key(event):
    btn_login.invoke()  # Simulate a click on the login button
 
'''
# Main application logic starts here
'''
# User database dictionary
users_db = {}
 
# # Ready CSV to accept data
# initialize_csv_file()
 
# Load users into dictionary
load_users()
 
# Initialize flags to handle device connecting
first_device_flag = False
device_compare_flag = False
 
 
# Main GUI window, initialize properties
root = tk.Tk()
root.title("Pacemaker DCM")
root.geometry("500x400")  
root.configure(bg="#f0f0f0")

# Welcome message
welcome_message = tk.Label(root, text="\n\tWelcome\n", font=("Cambria", 24, "bold"), bg="#f0f0f0")
welcome_message.grid(row=0, column=0, columnspan=3, pady=(20, 0),)  # Cente#AA0000 by columnspan
 
welcome_message2 = tk.Label(root, text="\t               Please Login or Register Below", font=("Cambria", 12), bg="#f0f0f0")
welcome_message2.grid(row=1, column=0, columnspan=3, pady=(0, 30))  
 
# Name label and entry
lbl_name = tk.Label(root, text="Name:", bg="#f0f0f0")
lbl_name.grid(row=2, column=0, padx=(100, 0), pady=5)  
entry_name = tk.Entry(root, width=30)
entry_name.grid(row=2, column=1, padx=(0, 0), pady=5)  
 
# Password label and entry
lbl_password = tk.Label(root, text="Password:", bg="#f0f0f0")
lbl_password.grid(row=3, column=0, padx=(100, 0), pady=5)  
entry_password = tk.Entry(root, show="*", width=30)  
entry_password.grid(row=3, column=1, padx=(0, 0), pady=5)  
 
# Register button
btn_register = tk.Button(root, text="Register", command=register_user, bg="#4CAF50", fg="green", width=10, height = 1)
btn_register.grid(row=4, column=1, padx=(0, 0), pady=20, sticky="e")
 
# Login button with green outline
btn_login = tk.Button(root, text="Login", command=login_user, bg="white", fg="green", width=10, height = 1)
btn_login.grid(row=4, column=1, padx=(0, 0), pady=20, sticky="w")
 
# Bind the Enter key to trigger the login button
root.bind('<Return>', on_login_enter_key)

def show_login_screen():
    clear_window()  # Clear the window
    
    # Recreate and display the login screen content
    root.title("Pacemaker DCM")
    root.geometry("500x400")
    root.configure(bg="#f0f0f0")

    # Welcome message
    welcome_message = tk.Label(root, text="\n\tWelcome\n", font=("Cambria", 24, "bold"), bg="#f0f0f0")
    welcome_message.grid(row=0, column=0, columnspan=3, pady=(20, 0))  # Cente#AA0000 by columnspan
    
    welcome_message2 = tk.Label(root, text="\t               Please Login or Register Below", font=("Cambria", 12), bg="#f0f0f0")
    welcome_message2.grid(row=1, column=0, columnspan=3, pady=(0, 30))  
    
    # Name label and entry (Global variables for later use)
    lbl_name = tk.Label(root, text="Name:", bg="#f0f0f0")
    lbl_name.grid(row=2, column=0, padx=(100, 0), pady=5)
    global entry_name
    entry_name = tk.Entry(root, width=30)
    entry_name.grid(row=2, column=1, padx=(0, 0), pady=5)  

    # Password label and entry
    lbl_password = tk.Label(root, text="Password:", bg="#f0f0f0")
    lbl_password.grid(row=3, column=0, padx=(100, 0), pady=5)
    global entry_password
    entry_password = tk.Entry(root, show="*", width=30)
    entry_password.grid(row=3, column=1, padx=(0, 0), pady=5)  
    
    # Register button (Global variables for later use)
    global btn_register
    btn_register = tk.Button(root, text="Register", command=register_user, bg="#4CAF50", fg="green", width=10, height=1)
    btn_register.grid(row=4, column=1, padx=(0, 0), pady=20, sticky="e")

    # Login button with green outline (Global variables for later use)
    global btn_login
    btn_login = tk.Button(root, text="Login", command=login_user, bg="white", fg="green", width=10, height=1)
    btn_login.grid(row=4, column=1, padx=(0, 0), pady=20, sticky="w")

    # Bind the Enter key to trigger the login button
    root.bind('<Return>', on_login_enter_key)
    
# Start the main event loop
root.mainloop()