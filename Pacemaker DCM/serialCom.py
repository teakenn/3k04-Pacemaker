import serial 
import serial.tools.list_ports
import struct

firstByte = 22
send = 13+6
echo = 22 + 6
get_egram = 47 + 6

# Send parameters to pacemaker, accepts parameters
def send_parameters(params,currPort):
    st = struct.Struct('<bbBBfBfBBBBBBBBBBfB')
    send_data = st.pack(firstByte,send,params["mode"],params["atr_pw"],params["atr_amp"],
            params["vent_pw"],params["vent_amp"],params["lrl"],params["url"],
            params["arp"],params["vrp"],params["atr_sens"],params["vent_sens"],
            params["rate_adapt"],params["msr"],params["reaction_time"],params["recovery_time"],
            params["act_thresh"],params["response_fact"])

    with serial.Serial(currPort, baudrate=115200,timeout=1) as ser:
        ser.write(send_data)
        ser.close()

# Read sent parameters from pacemaker
def read_params(params,currPort):
    st = struct.Struct('<bbBBfBfBBBBBBBBBBfB')
    send_data = st.pack(firstByte,echo,params["mode"],params["atr_pw"],params["atr_amp"],
            params["vent_pw"],params["vent_amp"],params["lrl"],params["url"],
            params["arp"],params["vrp"],params["atr_sens"],params["vent_sens"],
            params["rate_adapt"],params["msr"],params["reaction_time"],params["recovery_time"],
            params["act_thresh"],params["response_fact"])

    with serial.Serial(currPort, baudrate=115200,timeout=1) as ser:
        ser.write(send_data)
        curr_params = ser.read(42) # reading from pacemaker
        ser.close()

    return curr_params # returns list of current parameters

# begins and ends communication of egram data, accepts bool send_data
def get_plotData(ser,params):
    st = struct.Struct('<BBfBfBBBBBBBBBBfB')
    send_data = b'\x16' + b'\x47' + st.pack(params["mode"],params["atr_pw"],params["atr_amp"],
            params["vent_pw"],params["vent_amp"],params["lrl"],params["url"],
            params["arp"],params["vrp"],params["atr_sens"],params["vent_sens"],
            params["rate_adapt"],params["msr"],params["reaction_time"],params["recovery_time"],
            params["act_thresh"],params["response_fact"])

    ser.write(send_data)
    data = ser.read(32)
    st_read = struct.Struct('<dd')
    unpacked = st_read.unpack(data)

    try:
        voltage = unpacked
    except IndexError:
        print("No data found")
        return None

    return voltage



# ports = list(serial.tools.list_ports.comports())
# currPort = None

# # To find port pacemaker is connected to:
# for port in ports:
#     print(port.description)

#     if "JLink" in port.description: 
#         currPort = port.device
#         break

# if currPort:
#     print(f"Device is connected to: {currPort}")
# else:
#     print("Device not found.")

# mode = struct.pack('B', params["mode"]) # B = 1 byte uint8
    # rate_adapt = struct.pack('B', params["rate_adapt"])
    # lrl = struct.pack('B', params["lrl"]) 
    # url = struct.pack('B',params["url"])
    # vent_amp = struct.pack('f',params["vent_amp"]) # f = 4 bytes 32-bit float
    # vent_pw = struct.pack('f', params["vent_pw"])
    # atr_amp = struct.pack('f', params["atr_amp"]) 
    # atr_pw =  struct.pack('f', params["atr_pw"]) 
    # vent_sens = struct.pack('f', params["vent_sens"])
    # atr_sens = struct.pack('f', params["atr_sens"])
    # vrp = struct.pack('B', params["vrp"])
    # arp = struct.pack('B', params["arp"]) 
    # pvarp = struct.pack('B', params["pvarp"])
    # act_thresh = struct.pack('f',params["act_thresh"])
    # reaction_time = struct.pack('H', params["reaction_time"]) # H = 2 bytes uint16
    # resp_fact = struct.pack('f',params["response_fact"])
    # recovery_time = struct.pack('H', params["recovery_time"])
    # msr = struct.pack('B', params["msr"])

# # Reads user file and returns inputted parameters
# def get_csvData(user):
#     filename = f"{user}.csv" 
#     try:
#         with open(filename, mode = 'r') as file:
#             reader = csv.reader(file)
#             header = next(reader)
#             firstline = next(reader)
#             print(f"Successfully read {filename}")
#             return firstline
#     except FileNotFoundError:
#         print(f"File {filename}.csv not found.")
#         return None 
#     except StopIteration:
#         print("CSV file is empty or has no data rows.")
#         return None
#     except Exception as e:
#         print(f"An error occured: {e}")
#         return None
        






    

