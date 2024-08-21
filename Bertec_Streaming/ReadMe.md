
# What does this 'Bertec_Streaming' Folder do: 
This folder contains scripts that come together to stream Bertec Forceplate data via ZmQ pub-sub to a Controller. The GRF data is filtered using a real-time lowpass filter.

The file to be run is: 'gather_forcedata_Vicon.py'.

# Where and How should it be run: 
This folder should be on the Vicon computer to stream Bertec Forceplate data to the Raspberry Pi/Controller. 
The Vicon Nexus Application should be open as well to faciliate streaming of data.
Be sure to modify the system paths to reflect the location of this folder on your local desktop. 
** Note: Append path to the vicon_dssdk folder OR copy it to this Bertec_Streaming folder to enable interfacing with the Vicon Nexus App
