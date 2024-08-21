import sys 
sys.path.append(r"C:/Users/nundinir/Desktop/Bertec_Streaming_GSE/vicon_dssdk")

from vicon_dssdk import ViconDataStream
from time import sleep

class ViconSDK_Wrapper:
    '''
    Python module to communicate with ViconDataStreamSDK. 
    Grace Yi, Kevin Best 2022. 
    '''
    def __init__(self, vicon_IP='ROB-ROUSE-VICON.adsroot.itcs.umich.edu', viconPort='801'):
        self.client = ViconDataStream.Client()
        # Continually try to connect. Should probably timeout but that's a later problem
        while not self.client.IsConnected():
            self.client.Connect( vicon_IP + ':' + viconPort )
        print( 'Connected to Vicon at ' + vicon_IP + ':' + viconPort )

        # Enable streaming device data. Could enable other data here too. 
        self.client.EnableDeviceData()
        self.lastZForce = 0
        sleep(0.2)
        self.client.GetFrame()
        forceplate_to_vicon_latency=self.client.GetLatencyTotal()
        # print("Streaming Latency: {}\n".format(forceplate_to_vicon_latency))
        sleep(0.2)

    def get_streaming_latency(self):
        return self.client.GetLatencyTotal()
    
    def get_latest_device_values(self, forceplate_name_list = ["Hexapod"], output_names = ["Force"], component_names = ["Fz"]):
        """
        Gets the 
        For now, this method just returns everything in one big flat list. 
        Values are sorted first by forceplate, then by output_names, and then by component. 
        """
        self.client.GetFrame()
        results = []
        for plate_name in forceplate_name_list:
            for output_name in output_names:
                for component_name in component_names:
                    (retData,interpdFrame) = self.client.GetDeviceOutputValues(plate_name,output_name, component_name)
                    results.append(retData[-1])

        return results


if __name__=='__main__':
    client = ViconSDK_Wrapper('ROB-ROUSE-VICON.adsroot.itcs.umich.edu')
    for i in range(100):
        print(client.get_latest_device_values( ["RightForcePlate", "LeftForcePlate"], ["Force"], ["Fz"]),end='\n')
        sleep(0.01)