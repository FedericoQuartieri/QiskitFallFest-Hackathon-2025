from dotenv import load_dotenv
import os
import math
import random
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_aer import AerSimulator

load_dotenv()  # Load the environment variables from .env
token_imported = False

def import_token():
    global service
    my_token = os.getenv("MY_SECRET_TOKEN")
    if my_token is None:
        raise ValueError("Token not found in environment variables")

    service = QiskitRuntimeService(
        channel="ibm_cloud",
        token=my_token,
        instance=os.getenv("IBM_QUANTUM_INSTANCE")  # ad es. messo nella .env
    )

def back(prov):
    if (prov != "ibm"):
        return AerSimulator(method=prov)
    else:
        if not token_imported: import_token()
        backend = service.least_busy(operational=True, simulator=False)
        return backend
