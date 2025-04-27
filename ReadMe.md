This package is structured as follows:

    Exoboot-Controller-VAS/
        __init__.py
        Exoboot_Wrapper.py            # Main controller logic
        .gitignore

        src/
            settings/
                __init__.py
                constants.py  # Constants used across the project
                config.py     # Configuration settings
    
            exo/
                __init__.py
                ExoClass_thread.py             # Exoboot thread logic
                AssistanceGenerator_new.py     # Assistance generation logic
                TransmissionRatioGenerator.py  # Transmission ratio logic
                thermal.py                     # Thermal model
                GaitStateEstimator_thread.py   # Gait state logic
    
                gait_state_estimator/
                    IMU/
                        __init__.py
                        COMING SOON TO THEATERS....
                    Forceplate/
                        __init__.py
                        GroundContact.py    # Forceplate thresholding for stride period
                        BertecMan.py        # Bertec read/write class
                        ZMQ_PubSub.py       # ZMQ communication class 
    
            GUI_communication/
                __init__.py
                exoboot_remote.proto        # Protocol buffer definition
                exoboot_remote_pb2.py       # Generated protobuf code
                exoboot_remote_pb2_grpc.py  # gRPC service definitions
                exoboot_remote_control.py   # gRPC server and client logic
    
            logging/
                __init__.py
                LoggingClass.py  # Logging utilities
                FilingCabinet    # Organizing Subject Data Files
    
            utils/
                __init__.py
                utils.py         # General utility functions
                SoftRTloop.py    # Soft Real-time loop
    
            characterization/
                thermal_characterization/
                    __init__.py
                    thermal_characterization_STANDING.py
                    thermal_characterization_WALKING.py
    
                transmission_ratio_characterization/
                    __init__.py
                    TR_characterization_MAIN.py
    
                JIM_characterization/
                    JIM_testing_current_cmd.py
    
            debugging_scripts/
                __init__.py
    
            hud/
                __init__.py
                hud_thread.py
                exohud_layout.json
