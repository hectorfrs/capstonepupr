/
├── config/                  # Archivos de configuración
│   └── pi1_config.yaml      # Configuración principal del Raspberry Pi #1
├── lib/                     # Módulos de control y lógica de sensores
│   ├── mux_controller.py    # Controlador del MUX I²C
│   └── as7265x.py           # Manejador para los sensores AS7265x
├── utils/                   # Funcionalidades auxiliares
│   ├── mqtt_publisher.py    # Cliente MQTT
│   ├── greengrass.py        # Interacción con AWS Greengrass
│   ├── networking.py        # Manejo de red (Ethernet/Wi-Fi)
│   └── json_manager.py      # Gestión de datos JSON
├── logs/                    # Archivos de logs
│   └── pi1_logs.log         # Log principal del sistema
├── data/                    # Almacenamiento de datos temporales
│   └── spectral_data.json   # Datos JSON de mediciones espectroscópicas
├── main_pi1.py              # Script principal del sistema
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Documentación del proyecto
