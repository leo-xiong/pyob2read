 #!/usr/bin/env python

def maf(code):
    code = int(code,16)
    return code * 0.00132276

def throttle_pos(code):
    code = int(code,16)
    return code * 100.0 / 255.0

def intake_m_pres(code): # in kPa
    code = int(code,16)
    #return code / 0.14504
    return code
    
def rpm(code):
    code = int(code,16)
    return code / 4

def speed(code):
    code = int(code,16)
    return code / 1.609

def percent_scale(code):
    code = int(code,16)
    return code * 100.0 / 255.0

def timing_advance(code):
    code = int(code,16)
    return (code - 128) / 2.0

def sec_to_min(code):
    code = int(code,16)
    return code / 60

def temp(code):
    code = int(code,16)
    return code - 40 

def cpass(code):
    #fixme
    return code

def fuel_trim_percent(code):
    code = int(code,16)
    return (code - 128.0) * 100.0 / 128.0

def fuel_trim_percent_sensor(code):
    code = int(code,16)
    return (code - 256) * 100.0 / 256

def dtc_decrypt(code):
    num = int(code[0],16)
    if num & 1: # is mil light on
        mil = 1
    else:
        mil = 0
    # bit 0-6 are the number of dtc's. 
    num = num >> 1
    return (num, mil)

def hex_to_bitstring(str):
   n=int(str,16)
   return bin(n)[2:]

class Sensor:
    def __init__(self,sensorName, sensorcommand, sensorValueFunction, u):
        self.name = sensorName
        self.cmd  = sensorcommand
        self.value= sensorValueFunction
        self.unit = u

SENSORS = [
    Sensor("          Supported PIDs", "0100", hex_to_bitstring  ,""       ),    
    Sensor("Status Since DTC Cleared", "0101", dtc_decrypt       ,""       ),    
    Sensor("DTC Causing Freeze Frame", "0102", cpass             ,""       ),    
    Sensor("      Fuel System Status", "0103", cpass             ,""       ),
    Sensor("   Calculated Load Value", "0104", percent_scale     ,""       ),    
    Sensor("     Coolant Temperature", "0105", temp              ,"C"      ),
    Sensor("    Short Term Fuel Trim Bank 1", "0106", fuel_trim_percent ,"%"      ),
    Sensor("     Long Term Fuel Trim Bank 1", "0107", fuel_trim_percent ,"%"      ),
    Sensor("    Short Term Fuel Trim Bank 2", "0108", fuel_trim_percent ,"%"      ),
    Sensor("     Long Term Fuel Trim Bank 2", "0109", fuel_trim_percent ,"%"      ),
    Sensor("      Fuel Rail Pressure", "010A", cpass             ,""       ),
    Sensor("Intake Manifold Pressure", "010B", intake_m_pres     ,"kPa"    ),
    Sensor("              Engine RPM", "010C", rpm               ,""       ),
    Sensor("           Vehicle Speed", "010D", speed             ,"MPH"    ),
    Sensor("          Timing Advance", "010E", timing_advance    ,"degrees"),
    Sensor("         Intake Air Temp", "010F", temp              ,"C"      ),
    Sensor("     Air Flow Rate (MAF)", "0110", maf               ,"lb/min" ),
    Sensor("       Throttle Position", "0111", throttle_pos      ,"%"      ),
    Sensor("    Secondary Air Status", "0112", cpass             ,""       ),
    Sensor("  Location of O2 sensors", "0113", cpass             ,""       ),
    Sensor("        O2 Sensor: 1 - 1", "0114", fuel_trim_percent_sensor ,"%"      ),
    Sensor("        O2 Sensor: 1 - 2", "0115", fuel_trim_percent_sensor ,"%"      ),
    Sensor("        O2 Sensor: 1 - 3", "0116", fuel_trim_percent ,"%"      ),
    Sensor("        O2 Sensor: 1 - 4", "0117", fuel_trim_percent ,"%"      ),
    Sensor("        O2 Sensor: 2 - 1", "0118", fuel_trim_percent ,"%"      ),
    Sensor("        O2 Sensor: 2 - 2", "0119", fuel_trim_percent ,"%"      ),
    Sensor("        O2 Sensor: 2 - 3", "011A", fuel_trim_percent ,"%"      ),
    Sensor("        O2 Sensor: 2 - 4", "011B", fuel_trim_percent ,"%"      ),
    Sensor("         OBD Designation", "011C", cpass             ,""       ),
    Sensor("  Location of O2 sensors", "011D", cpass             ,""       ),
    Sensor("        Aux input status", "011E", cpass             ,""       ),
    Sensor(" Time Since Engine Start", "011F", sec_to_min        ,"min"    ),
    Sensor("  Engine Run with MIL on", "014E", sec_to_min        ,"min"    ),

    ]
     
    
#___________________________________________________________

def test():
    for i in SENSORS:
        print i.name, i.value("F")

if __name__ == "__main__":
    test()
