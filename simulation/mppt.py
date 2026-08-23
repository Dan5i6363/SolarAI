import numpy as np
import matplotlib.pyplot as plt

from pv_model import pv_model, find_mpp


# ============================================================
# P&O MPPT SIMULATION
# ============================================================

# MPPT settings
V_START = 10.0
V_MIN = 1.0
V_MAX = 21.5

V_STEP = 0.10

NUM_ITERATIONS = 250


def get_pv_power(voltage, irradiance, temperature):
    """
    Obtain PV current and power at a requested operating voltage.
    """

    pv_voltage, pv_current, pv_power = pv_model(
        irradiance=irradiance,
        temperature=temperature,
        num_points=2000
    )

    current = np.interp(
        voltage,
        pv_voltage,
        pv_current
    )

    power = voltage * current

    return current, power


def perturb_and_observe(
    irradiance=1000.0,
    temperature=25.0,
    num_iterations=NUM_ITERATIONS
):
    """
    Perturb and Observe MPPT algorithm.

    Returns:
        voltage_history
        current_history
        power_history
    """

    voltage = V_START

    previous_power = 0.0
    previous_voltage = voltage

    direction = 1

    voltage_history = []
    current_history = []
    power_history = []

    for iteration in range(num_iterations):

        # ----------------------------------------------------
        # Measure PV electrical values
        # ----------------------------------------------------

        current, power = get_pv_power(
            voltage,
            irradiance,
            temperature
        )

        voltage_history.append(voltage)
        current_history.append(current)
        power_history.append(power)

        # ----------------------------------------------------
        # First measurement
        # ----------------------------------------------------

        if iteration == 0:

            previous_power = power
            previous_voltage = voltage

            voltage += direction * V_STEP

            continue

        # ----------------------------------------------------
        # Perturb and Observe logic
        # ----------------------------------------------------

        delta_power = power - previous_power

        delta_voltage = voltage - previous_voltage

        if delta_power > 0:

            # Power increased.
            # Continue moving in the same direction.

            if delta_voltage > 0:
                direction = 1
            else:
                direction = -1

        elif delta_power < 0:

            # Power decreased.
            # Reverse direction.

            direction *= -1

        else:

            # No significant change.
            direction *= -1

        # ----------------------------------------------------
        # Update operating voltage
        # ----------------------------------------------------

        previous_voltage = voltage
        previous_power = power

        voltage += direction * V_STEP

        # Voltage limits
        voltage = np.clip(
            voltage,
            V_MIN,
            V_MAX
        )

    return (
        np.array(voltage_history),
        np.array(current_history),
        np.array(power_history)
    )


def run_test(irradiance, temperature):

    print()
    print("============================================")
    print("             P&O MPPT TEST")
    print("============================================")
    print(f"Irradiance     : {irradiance:.0f} W/m^2")
    print(f"Temperature    : {temperature:.1f} deg C")
    print("--------------------------------------------")

    # Theoretical PV curve
    pv_voltage, pv_current, pv_power = pv_model(
        irradiance,
        temperature
    )

    theoretical_vmp, theoretical_imp, theoretical_pmp = find_mpp(
        pv_voltage,
        pv_current,
        pv_power
    )

    # Run P&O
    voltage_history, current_history, power_history = (
        perturb_and_observe(
            irradiance,
            temperature
        )
    )

    # Best tracked point
    best_index = np.argmax(power_history)

    tracked_voltage = voltage_history[best_index]
    tracked_current = current_history[best_index]
    tracked_power = power_history[best_index]

    # MPPT efficiency
    efficiency = (
        tracked_power / theoretical_pmp
    ) * 100.0

    print(f"Theoretical Vmp: {theoretical_vmp:.2f} V")
    print(f"Theoretical Pmp: {theoretical_pmp:.2f} W")
    print("--------------------------------------------")
    print(f"Tracked Vmp    : {tracked_voltage:.2f} V")
    print(f"Tracked Power  : {tracked_power:.2f} W")
    print(f"MPPT Efficiency: {efficiency:.2f} %")
    print("============================================")

    return (
        voltage_history,
        power_history,
        theoretical_vmp,
        theoretical_pmp
    )


if __name__ == "__main__":

    # --------------------------------------------------------
    # TEST 1: Standard Test Condition
    # --------------------------------------------------------

    (
        voltage_history,
        power_history,
        theoretical_vmp,
        theoretical_pmp
    ) = run_test(
        irradiance=1000.0,
        temperature=25.0
    )

    # --------------------------------------------------------
    # MPPT voltage tracking plot
    # --------------------------------------------------------

    plt.figure(figsize=(8, 5))

    plt.plot(
        voltage_history,
        label="P&O Operating Voltage"
    )

    plt.axhline(
        theoretical_vmp,
        linestyle="--",
        label=f"Theoretical Vmp = {theoretical_vmp:.2f} V"
    )

    plt.xlabel("Iteration")
    plt.ylabel("Voltage (V)")
    plt.title("P&O MPPT Voltage Tracking")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "plots/mppt_voltage_tracking.png",
        dpi=300
    )

    plt.show()

    # --------------------------------------------------------
    # MPPT power tracking plot
    # --------------------------------------------------------

    plt.figure(figsize=(8, 5))

    plt.plot(
        power_history,
        label="P&O Output Power"
    )

    plt.axhline(
        theoretical_pmp,
        linestyle="--",
        label=f"Theoretical Pmp = {theoretical_pmp:.2f} W"
    )

    plt.xlabel("Iteration")
    plt.ylabel("Power (W)")
    plt.title("P&O MPPT Power Tracking")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "plots/mppt_power_tracking.png",
        dpi=300
    )

    plt.show()

    # --------------------------------------------------------
    # PV P-V curve + MPPT operating points
    # --------------------------------------------------------

    pv_voltage, pv_current, pv_power = pv_model(
        1000.0,
        25.0
    )

    plt.figure(figsize=(8, 5))

    plt.plot(
        pv_voltage,
        pv_power,
        label="PV P-V Curve"
    )

    plt.scatter(
        voltage_history,
        power_history,
        s=8,
        label="P&O Operating Points"
    )

    plt.scatter(
        theoretical_vmp,
        theoretical_pmp,
        s=60,
        label="Theoretical MPP"
    )

    plt.xlabel("Voltage (V)")
    plt.ylabel("Power (W)")
    plt.title("P&O MPPT Tracking on PV P-V Curve")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "plots/mppt_pv_curve.png",
        dpi=300
    )

    plt.show()
