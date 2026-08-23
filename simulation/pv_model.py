import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# SOLAR PV MODEL - PHASE I
# Datasheet-calibrated empirical model
# ============================================================

G_REF = 1000.0
T_REF = 25.0

# Selected 20 Wp panel parameters
P_RATED = 20.0
V_MP_REF = 18.20
I_MP_REF = 1.10
V_OC_REF = 22.40
I_SC_REF = 1.45

# Approximate temperature coefficients.
# Replace with manufacturer values when available.
VOC_TEMP_COEFF = -0.0025
ISC_TEMP_COEFF = 0.0005


def pv_model(irradiance=1000.0, temperature=25.0, num_points=2000):

    G = max(float(irradiance), 0.0)
    T = float(temperature)

    if G <= 0:
        voltage = np.linspace(0.0, V_OC_REF, num_points)
        current = np.zeros_like(voltage)
        power = np.zeros_like(voltage)
        return voltage, current, power

    # Environmental scaling
    g_ratio = G / G_REF
    delta_t = T - T_REF

    # Current scales approximately with irradiance
    isc = I_SC_REF * g_ratio
    imp = I_MP_REF * g_ratio

    # Temperature effect on current
    isc *= 1.0 + ISC_TEMP_COEFF * delta_t
    imp *= 1.0 + ISC_TEMP_COEFF * delta_t

    # Temperature effect on voltage
    voc = V_OC_REF * (
        1.0 + VOC_TEMP_COEFF * delta_t
    )

    vmp = V_MP_REF * (
        1.0 + VOC_TEMP_COEFF * delta_t
    )

    # Small logarithmic irradiance effect on voltage
    if g_ratio > 0:
        voltage_shift = 0.50 * np.log(g_ratio)
        voc += voltage_shift
        vmp += 0.70 * voltage_shift

    voc = max(voc, 0.1)
    vmp = min(vmp, voc * 0.98)

    # Voltage samples
    voltage = np.linspace(0.0, voc, num_points)

    current = np.zeros_like(voltage)

    # --------------------------------------------------------
    # Region 1: 0 <= V <= Vmp
    #
    # Exponent chosen so the power derivative becomes zero
    # at Vmp.
    # --------------------------------------------------------

    region1 = voltage <= vmp

    exponent_1 = imp / max(isc - imp, 1e-9)

    x1 = voltage[region1] / vmp

    current[region1] = (
        isc
        - (isc - imp) * x1 ** exponent_1
    )

    # --------------------------------------------------------
    # Region 2: Vmp < V <= Voc
    #
    # The exponent is chosen to maintain the MPP condition
    # at Vmp while forcing current to zero at Voc.
    # --------------------------------------------------------

    region2 = voltage > vmp

    x2 = (
        voltage[region2] - vmp
    ) / (
        voc - vmp
    )

    exponent_2 = (
        (voc - vmp) / vmp
    )

    current[region2] = (
        imp * np.maximum(1.0 - x2, 0.0) ** exponent_2
    )

    current = np.maximum(current, 0.0)

    # Exact endpoints
    current[0] = isc
    current[-1] = 0.0

    # Power
    power = voltage * current

    return voltage, current, power


def find_mpp(voltage, current, power):

    index = np.argmax(power)

    return (
        voltage[index],
        current[index],
        power[index]
    )


def print_result(irradiance, temperature):

    voltage, current, power = pv_model(
        irradiance,
        temperature
    )

    v_mpp, i_mpp, p_mpp = find_mpp(
        voltage,
        current,
        power
    )

    reference_power = V_MP_REF * I_MP_REF

    power_error = (
        (p_mpp - reference_power)
        / reference_power
    ) * 100.0

    voltage_error = (
        (v_mpp - V_MP_REF)
        / V_MP_REF
    ) * 100.0

    current_error = (
        (i_mpp - I_MP_REF)
        / I_MP_REF
    ) * 100.0

    print()
    print("============================================")
    print("       SOLAR PV MODEL - PHASE I")
    print("============================================")
    print("Panel          : Selected 20 Wp module")
    print(f"Irradiance     : {irradiance:.0f} W/m^2")
    print(f"Temperature    : {temperature:.1f} deg C")
    print("--------------------------------------------")
    print(f"Rated Power    : {P_RATED:.2f} W")
    print(f"Simulated MPP  : {p_mpp:.2f} W")
    print(f"MPP Voltage    : {v_mpp:.2f} V")
    print(f"MPP Current    : {i_mpp:.2f} A")
    print("--------------------------------------------")
    print(f"Reference Vmp  : {V_MP_REF:.2f} V")
    print(f"Reference Imp  : {I_MP_REF:.2f} A")
    print(f"Reference Pmp  : {reference_power:.2f} W")
    print(f"Reference Voc  : {V_OC_REF:.2f} V")
    print(f"Reference Isc  : {I_SC_REF:.2f} A")
    print("--------------------------------------------")
    print(f"Power error    : {power_error:+.3f} %")
    print(f"Voltage error  : {voltage_error:+.3f} %")
    print(f"Current error  : {current_error:+.3f} %")
    print("============================================")


if __name__ == "__main__":

    # STC test
    voltage, current, power = pv_model(
        irradiance=1000.0,
        temperature=25.0
    )

    v_mpp, i_mpp, p_mpp = find_mpp(
        voltage,
        current,
        power
    )

    print_result(1000.0, 25.0)

    # --------------------------------------------------------
    # I-V curve
    # --------------------------------------------------------

    plt.figure(figsize=(8, 5))

    plt.plot(
        voltage,
        current,
        label="Simulated I-V"
    )

    plt.scatter(
        V_MP_REF,
        I_MP_REF,
        label="Manufacturer MPP"
    )

    plt.xlabel("Voltage (V)")
    plt.ylabel("Current (A)")
    plt.title("20 Wp PV Module - I-V Characteristic")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "plots/pv_iv_curve.png",
        dpi=300
    )

    plt.show()

    # --------------------------------------------------------
    # P-V curve
    # --------------------------------------------------------

    plt.figure(figsize=(8, 5))

    plt.plot(
        voltage,
        power,
        label="Simulated P-V"
    )

    plt.scatter(
        V_MP_REF,
        V_MP_REF * I_MP_REF,
        label="Manufacturer MPP"
    )

    plt.xlabel("Voltage (V)")
    plt.ylabel("Power (W)")
    plt.title("20 Wp PV Module - P-V Characteristic")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "plots/pv_pv_curve.png",
        dpi=300
    )

    plt.show()
