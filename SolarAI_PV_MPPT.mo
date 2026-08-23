package PhotoVoltaics
  extends Modelica.Icons.Package;

  package Examples "Examples"
    extends Modelica.Icons.ExamplesPackage;

    model SimpleModuleMPDC "Simple module supplies DC grid with maximum power tracker"
      extends Modelica.Icons.Example;
      Modelica.Electrical.Analog.Basic.Ground groundDC;
      PhotoVoltaics.Components.SimplePhotoVoltaics.SimpleModuleSymmetric module(moduleData = moduleData, T = 298.15, useConstantIrradiance = false);
      PhotoVoltaics.Components.Converters.DCConverter converter;
      PhotoVoltaics.Components.Blocks.MPTrackerSample mpTracker(VmpRef = moduleData.VmpRef, ImpRef = moduleData.ImpRef, samplePeriod = 10);
      Modelica.Electrical.Analog.Basic.Ground ground;
      Modelica.Electrical.Analog.Sensors.PowerSensor powerSensor;
      parameter PhotoVoltaics.Records.SHARP_NU_S5_E3E moduleData;
      PhotoVoltaics.Sources.Electrical.IdealBattery battery(ns = 4, np = 1, V1Cell = 14, V0Cell = 11, ECell = 12*100*3600, allowOvercharge = true, allowUndercharge = true, ViniCell = 11);
      PhotoVoltaics.Sources.Irradiance.Irradiance irradiance;
    equation
      connect(groundDC.p, module.n);
      connect(mpTracker.vRef, converter.vDCRef);
      connect(module.p, powerSensor.pc);
      connect(mpTracker.power, powerSensor.power);
      connect(powerSensor.pc, powerSensor.pv);
      connect(powerSensor.nv, groundDC.p);
      connect(battery.pin_n, ground.p);
      connect(irradiance.irradiance, module.variableIrradiance);
      connect(groundDC.p, converter.dc_n1);
      connect(converter.dc_p1, powerSensor.nc);
      connect(converter.dc_p2, battery.pin_p);
      connect(converter.dc_n2, ground.p);
      annotation(experiment(StopTime = 86400, Interval = 1, Tolerance = 1e-06, StartTime = 0), __OpenModelica_simulationFlags(jacobian = "coloredNumerical", nls = "newton", s = "dassl", lv = "LOG_STATS"));
    end SimpleModuleMPDC;
  end Examples;

  package Components "Components"
    extends Modelica.Icons.Package;

    package SimplePhotoVoltaics "Photovoltaic cells, modules and plants"
      extends Modelica.Icons.Package;

      model SimpleModuleSymmetric "Simple module consisting of symmetric series connected cells"
        extends .PhotoVoltaics.Interfaces.PartialCell(diode(final m = m, final R = 1E8, final Bv = moduleData.BvCell, final Ibv = moduleData.Ibv, final Nbv = moduleData.Nbv, final IRef = moduleData.IscRef, final alphaI = moduleData.alphaIsc, final alphaV = moduleData.alphaVoc, final ns = moduleData.ns, final VRef = moduleData.VocCellRef, final nsModule = 1, final npModule = 1), signalCurrent(final IRef = IphRef, final irradianceRef = moduleData.irradianceRef, final alphaRef = moduleData.alphaIsc));
        final parameter Real m(start = 2, fixed = false) "Ideality factor of diode";
        final parameter Modelica.Units.SI.Current IsdRef(start = 1E-4, fixed = false) "Reference saturation current of cell";
        final parameter Modelica.Units.SI.Current IphRef = moduleData.IscRef "Reference photo current of cell";
        Modelica.Units.SI.Voltage vCell = v/moduleData.ns "Cell voltage";
        Modelica.Units.SI.Current iCell = i "Cell current";
        Modelica.Units.SI.Current iCellGenerating = -iCell "Negative cell current (generating)";
        Modelica.Units.SI.Power powerCell = vCell*iCell "Cell power";
        Modelica.Units.SI.Power powerCellGenerating = vCell*iCellGenerating "Negative power consumption (generating)";
      initial equation
        IphRef = IsdRef*(exp(moduleData.VocCellRef/m/moduleData.VtCellRef) - 1);
        IphRef = IsdRef*(exp(moduleData.VmpCellRef/m/moduleData.VtCellRef) - 1) + moduleData.ImpRef;
      end SimpleModuleSymmetric;
    end SimplePhotoVoltaics;

    package Converters "Converters"
      extends Modelica.Icons.Package;

      model DCConverter "DC controlled single phase DC/AC converter"
        extends Modelica.Electrical.PowerConverters.Interfaces.DCDC.DCtwoPin1;
        extends Modelica.Electrical.PowerConverters.Interfaces.DCDC.DCtwoPin2;
        extends .PhotoVoltaics.Icons.Converter;
        parameter Modelica.Units.SI.Voltage VRef = 48 "Reference DC source voltage";
        parameter Modelica.Units.SI.Time Ti = 1E-6 "Internal integration time constant";
        Modelica.Blocks.Interfaces.RealInput vDCRef(final unit = "V") "DC voltage";
        Modelica.Electrical.Analog.Sources.SignalVoltage signalVoltage;
        Modelica.Electrical.Analog.Sensors.CurrentSensor currentSensor;
        Modelica.Blocks.Math.Product product;
        Modelica.Blocks.Math.Feedback feedback;
        Modelica.Electrical.Analog.Sources.SignalCurrent variableCurrentSource;
        Modelica.Electrical.Analog.Sensors.PowerSensor powerSensor;
        Modelica.Blocks.Continuous.Integrator integrator(k = 1/VRef/Ti);
        Modelica.Blocks.Math.Gain gain(final k = -1);
      equation
        connect(currentSensor.n, signalVoltage.p);
        connect(signalVoltage.v, vDCRef);
        connect(currentSensor.i, product.u1);
        connect(vDCRef, product.u2);
        connect(product.y, feedback.u1);
        connect(feedback.y, integrator.u);
        connect(gain.y, feedback.u2);
        connect(gain.u, powerSensor.power);
        connect(powerSensor.nc, variableCurrentSource.n);
        connect(integrator.y, variableCurrentSource.i);
        connect(powerSensor.pv, powerSensor.pc);
        connect(currentSensor.p, dc_p1);
        connect(signalVoltage.n, dc_n1);
        connect(powerSensor.pc, dc_p2);
        connect(variableCurrentSource.p, dc_n2);
        connect(dc_n2, powerSensor.nv);
      end DCConverter;
    end Converters;

    package Diodes "Diodes"
      extends Modelica.Icons.Package;

      model Diode2Module "Diode model with four different sections including breakthrough"
        extends .PhotoVoltaics.Interfaces.PartialDiode;
        parameter Modelica.Units.SI.Voltage Bv = 5.1 "Breakthrough voltage";
        parameter Modelica.Units.SI.Current Ibv = 0.7 "Breakthrough knee current";
        parameter Real Nbv = 0.74 "Breakthrough emission coefficient";
        parameter Integer ns = 1 "Number of series connected cells per module";
        parameter Integer nsModule(final min = 1) = 1 "Number of series connected modules";
        parameter Integer npModule(final min = 1) = 1 "Number of parallel connected modules";
        final parameter Modelica.Units.SI.Voltage VtRef = Modelica.Constants.k*TRef/Q "Reference voltage equivalent of temperature";
        final parameter Modelica.Units.SI.Voltage VBv = (-m*Nbv*log(IdsRef*Nbv/Ibv)*VtRef) - Bv "Voltage limit of approximation of breakthrough";
        final parameter Modelica.Units.SI.Current IdsRef = IRef/(exp(VRef/m/VtRef) - 1) "Reference saturation current";
        final parameter Modelica.Units.SI.Voltage VNegLin = (-VRef/m/VtRef*(Nbv*m*VtRef)) - Bv "Limit of linear range left of breakthrough";
        Modelica.Units.SI.Voltage VNeg "Limit of linear negative voltage range";
        Modelica.Units.SI.Voltage vCell = v/ns/nsModule "Cell voltage";
        Modelica.Units.SI.Voltage vModule = v/nsModule "Module voltage";
        Modelica.Units.SI.Current iModule = i/npModule "Module current";
        constant Integer MaxExp = 30;
      equation
        VNeg = m*Vt*log(Vt/VtRef);
        i/npModule = smooth(1, if v/ns/nsModule > VNeg then Ids*(Functions.exlin(v/ns/nsModule/m/Vt, MaxExp) - 1) + v/ns/nsModule/R elseif v/ns/nsModule > VBv then Ids*v/ns/nsModule/m/VtRef + v/ns/nsModule/R
         elseif v/ns/nsModule > VNegLin then (-Ibv*Functions.exlin(-(v/ns/nsModule + Bv)/(Nbv*m*Vt), MaxExp)) + Ids*VBv/m/VtRef + v/ns/nsModule/R else Ids*v/ns/nsModule/m/Vt - Ibv*Functions.exlin(VRef/m/VtRef, MaxExp)*(1 - (v/ns/nsModule + Bv)/(Nbv*m*Vt) - VRef/m/VtRef) + v/ns/nsModule/R);
      end Diode2Module;
    end Diodes;

    package Blocks "Blocks"
      extends Modelica.Icons.Package;

      block MPTrackerSample "Sampling maximum power tracker"
        extends Modelica.Blocks.Icons.Block;
        parameter Modelica.Units.SI.Time startTime = 0 "Start time";
        parameter Modelica.Units.SI.Time samplePeriod = 1 "Sample period";
        parameter Modelica.Units.SI.Voltage VmpRef "Reference maximum power power of plant";
        parameter Modelica.Units.SI.Current ImpRef "Reference maximum power current of plant";
        parameter Integer n = 100 "Number of voltage and power discretizations";
        final parameter Modelica.Units.SI.Voltage dv = VmpRef/n "Voltage change and maximum deviation";
        final parameter Modelica.Units.SI.Power dpower = VmpRef*ImpRef/n "Power change and maximum deviation";
        Boolean firstTrigger(start = false, fixed = true) "First boolean sample trigger signal";
        Boolean sampleTrigger "Boolean sample trigger signal";
        discrete Integer counter(final start = 0, fixed = true) "Sample counter";
        discrete Real signv(final start = -1, fixed = true) "Sign of voltage change";
        Modelica.Blocks.Interfaces.RealInput power(final unit = "W") "Power";
        Modelica.Blocks.Interfaces.RealOutput vRef(final unit = "V", final start = VmpRef, fixed = true) "Reference DC voltage";
      algorithm
        sampleTrigger := sample(startTime, samplePeriod);
        when sampleTrigger then
          counter := pre(counter) + 1;
          firstTrigger := time <= startTime + samplePeriod/2;
          vRef := pre(vRef) + signv*dv;
          if not firstTrigger and power < pre(power) then
            signv := -pre(signv);
          else
          end if;
          if vRef <= 3*dv then
            signv := 1;
          else
          end if;
        end when;
      end MPTrackerSample;
    end Blocks;
  end Components;

  package Functions "Functions"
    extends Modelica.Icons.Package;

    function limit "Limit input u by uMin and uMax"
      extends Modelica.Icons.Function;
      input Real u "Input to be limited";
      input Real uMin "Minimum of input";
      input Real uMax "Maximum of input";
      output Real y "Limited input";
    algorithm
      y := if u > uMax then uMax else if u < uMin then uMin else u;
    end limit;

    function degree "Convert radians into degrees"
      input Real rad "Angle in rad";
      output Real degree "Angle in degree";
    algorithm
      degree := rad*180/Modelica.Constants.pi;
    end degree;

    function rad "Convert degrees into radians"
      input Real deg "Angle in degree";
      output Real rad "Angle in rad";
    algorithm
      rad := deg*Modelica.Constants.pi/180;
    end rad;

    function dayOfTheYear "Determined day of the year based on date"
      input Integer day "Day";
      input Integer month "Month";
      input Integer year "Year";
      output Integer dayOfYear "Day of the year indicated by day, month, year";
    protected
      Boolean leapYear "Indicates leap year";
    algorithm
      leapYear := if mod(year, 4) == 0 then true else false;
      dayOfYear := day;
      dayOfYear := dayOfYear + (if month > 1 then 31 else 0);
      dayOfYear := dayOfYear + (if month > 2 then 28 + (if leapYear then 1 else 0) else 0);
      dayOfYear := dayOfYear + (if month > 3 then 31 else 0);
      dayOfYear := dayOfYear + (if month > 4 then 30 else 0);
      dayOfYear := dayOfYear + (if month > 5 then 31 else 0);
      dayOfYear := dayOfYear + (if month > 6 then 30 else 0);
      dayOfYear := dayOfYear + (if month > 7 then 31 else 0);
      dayOfYear := dayOfYear + (if month > 8 then 31 else 0);
      dayOfYear := dayOfYear + (if month > 9 then 30 else 0);
      dayOfYear := dayOfYear + (if month > 10 then 31 else 0);
      dayOfYear := dayOfYear + (if month > 11 then 30 else 0);
    end dayOfTheYear;

    function exlin "Exponential function linearly continued for x > Maxexp"
      extends Modelica.Icons.Function;
      input Real x;
      input Real Maxexp;
      output Real z;
    algorithm
      z := if x > Maxexp then exp(Maxexp)*(1 + x - Maxexp) else exp(x);
    end exlin;
  end Functions;

  package Sources "Sources"
    extends Modelica.Icons.Package;

    package Irradiance "Irradiance"
      extends Modelica.Icons.Package;

      model Irradiance "Simple solar irradiance without considering weather conditions"
        import Modelica.Constants.pi;
        import PhotoVoltaics.Functions.rad;
        import PhotoVoltaics.Functions.degree;
        import PhotoVoltaics.Functions.dayOfTheYear;
        parameter Integer startDay(final min = 1, final max = 31) = 10 "Day";
        parameter Integer startMonth(final min = 1, final max = 12) = 9 "Month";
        parameter Integer startYear = 2016 "Year";
        parameter Integer TimeZone = 1 "Time zone";
        parameter Modelica.Units.SI.Angle longitude = 0.2856929452589518 "Longitude";
        parameter Modelica.Units.SI.Angle latitude = 0.8418964085999744 "Latitude";
        parameter Modelica.Units.SI.Irradiance irradianceRef = 1000 "Reference solar irradiance";
        parameter Modelica.Units.SI.Angle gamma = 10*pi/180 "Angle of PV module with w.r.t. horizontal plane";
        parameter Modelica.Units.SI.Angle azimuth = 0 "Azimuth of the PV module orientation";
        Integer startDayOfYear(start = dayOfTheYear(startDay, startMonth, startYear), fixed = true) "Start day of year in simulation";
        Integer dayOfYear(final start = dayOfTheYear(startDay, startMonth, startYear), fixed = true) "Actual day of year";
        Integer daysOfYear(final start = dayOfTheYear(31, 12, startYear), fixed = true) "Total number of days of year";
        Integer year(final start = startYear, fixed = true) "Actual year";
        Modelica.Units.SI.Angle Jprime(final start = dayOfTheYear(startDay, startMonth, startYear)/dayOfTheYear(31, 12, startYear)*2*pi, fixed = true) "Equivalent Angle of the day of the year w.r.t. total number of days";
        Real delta_J;
        Real timeequation_J;
        Modelica.Units.NonSI.Time_day localTimeDays "Local time in days";
        Integer localDays "Locale day";
        Modelica.Units.SI.Time localTime "Local time";
        Modelica.Units.NonSI.Time_hour localTimeHours "Local time in unit hours";
        Modelica.Units.NonSI.Time_hour LocalMeanTimeHours "Local mean time in unit hours";
        Modelica.Units.NonSI.Time_hour trueMeanTimeHours "True mean time in unit hours";
        Modelica.Units.SI.Angle hoursAngle "Hours angle";
        Modelica.Units.SI.Angle sunHeight "Sun height";
        Modelica.Units.SI.Angle sunAzimuth1 "Sun azimuth before 12 p.m.";
        Modelica.Units.SI.Angle sunAzimuth2 "Sun azimuth after 12 p.m.";
        Modelica.Units.SI.Angle sunAzimuth "Sun azimuth";
        Modelica.Units.SI.Angle angleOfIncidence "Angle of incidence between a vector in sun direction and a normal vector";
        Modelica.Units.SI.Irradiance directIrradianceHorizontal "Direct irradiance on the horizontal in W/m^2";
        Modelica.Units.SI.Irradiance directIrradianceInclined "Direct irradiance on the inclined plane in w/m^2";
        Modelica.Blocks.Interfaces.RealOutput irradiance "Irradiance of inclined area";
      equation
        Jprime = dayOfYear/daysOfYear*2*pi;
        delta_J = rad(0.3948 - 23.2559*cos(Jprime + rad(9.1)) - 0.3915*cos(2*Jprime + rad(5.4)) - 0.1764*cos(3*Jprime + rad(26)));
        timeequation_J = 0.0066 + 7.3525*cos(Jprime + rad(85.9)) + 9.9359*cos(2*Jprime + rad(108.9)) + 0.3387*cos(3*Jprime + rad(105.2));
        localTime = time;
        localTimeHours = localTime/3600;
        localTimeDays = localTimeHours/24;
        localDays = integer(floor(localTimeDays));
        LocalMeanTimeHours = localTimeHours - TimeZone + 4/60*longitude*180/Modelica.Constants.pi;
        trueMeanTimeHours = LocalMeanTimeHours + timeequation_J/60;
        hoursAngle = rad((12 - trueMeanTimeHours)*15);
        sunHeight = degree(asin(cos(hoursAngle)*cos(latitude)*cos(delta_J) + sin(latitude)*sin(delta_J)))*(Modelica.Constants.pi/180);
        sunAzimuth1 = Modelica.Constants.pi - acos((sin(sunHeight)*sin(latitude) - sin(delta_J))/(cos(sunHeight)*cos(latitude)));
        sunAzimuth2 = Modelica.Constants.pi + acos((sin(sunHeight)*sin(latitude) - sin(delta_J))/(cos(sunHeight)*cos(latitude)));
        sunAzimuth = if mod(localTimeHours, 24) <= 12 then sunAzimuth1 else sunAzimuth2;
        angleOfIncidence = acos((-cos(sunHeight)*sin(gamma)*cos(sunAzimuth - azimuth)) + sin(sunHeight)*cos(gamma));
        directIrradianceHorizontal = if sunHeight < 0 then 0 else irradianceRef*sin(sunHeight);
        directIrradianceInclined = if angleOfIncidence > pi/2 then 0 else if abs(sin(sunHeight)) < 1E-5 then 0 else directIrradianceHorizontal*(cos(angleOfIncidence)/sin(sunHeight));
        irradiance = directIrradianceInclined;
      algorithm
        when sample(24*3600, 24*3600) then
          dayOfYear := mod(pre(dayOfYear), pre(daysOfYear)) + 1;
        end when;
        when startDayOfYear + localDays == daysOfYear + 1 then
          startDayOfYear := 1;
          year := pre(year) + 1;
          daysOfYear := dayOfTheYear(31, 12, year);
        end when;
      end Irradiance;
    end Irradiance;

    package Electrical "Electrical sources"
      extends Modelica.Icons.Package;

      model IdealBattery "Re-chargeable ideal battery without loss"
        parameter Integer ns(min = 1) = 1 "Number of series cells";
        parameter Integer np(min = 1) = 1 "Number of parallel cells";
        parameter Modelica.Units.SI.Voltage V1Cell "Maximum cell voltage > V0Cell";
        parameter Modelica.Units.SI.Voltage V0Cell "Minimum cell voltage < V1Cell";
        final parameter Modelica.Units.SI.Voltage V1 = V1Cell*ns "Maximum battery voltage > V0";
        final parameter Modelica.Units.SI.Voltage V0 = V0Cell*ns "Maximum battery voltage < V1";
        parameter Boolean allowOvercharge = false "Allows overcharging without error";
        parameter Boolean allowUndercharge = false "Allows undercharging without error";
        parameter Modelica.Units.SI.Energy ECell "Total cell energy between V0Cell and V1Cell";
        final parameter Modelica.Units.SI.Capacitance CCell = 2*ECell/(V1Cell^2 - V0Cell^2) "Total charge of battery";
        parameter Modelica.Units.SI.Voltage ViniCell = V1Cell "Initial cell voltage";
        Modelica.Units.SI.Voltage v = pin_p.v - pin_n.v "Battery voltage";
        Modelica.Units.SI.Voltage vCell = v/ns "Cell voltage";
        Modelica.Units.SI.Current i = capacitor.i "Battery current";
        Modelica.Units.SI.Current iCell = i/np "Cell current";
        Modelica.Units.SI.Power power = v*i "Battery power";
        Modelica.Units.SI.Power powerCell = power/ns/np "Cell power";
        Modelica.Units.SI.Energy energy "Energy";
        Modelica.Units.SI.Energy energyCell "Cell energy";
        Modelica.Electrical.Analog.Basic.Capacitor capacitor(final C = CCell*np/ns, v(start = ns*ViniCell, fixed = true));
        Modelica.Electrical.Analog.Interfaces.PositivePin pin_p "Positive pin";
        Modelica.Electrical.Analog.Interfaces.NegativePin pin_n "Negative pin";
      initial equation
        energyCell = CCell*(ViniCell^2 - V0Cell^2)/2;
      equation
        der(energy) = power;
        energyCell*ns*np = energy;
        assert(vCell >= V0Cell or allowUndercharge, "Battery: cell voltage less than V0Cell");
        assert(vCell <= V1Cell or allowOvercharge, "Battery: cell voltage greater than V1Cell");
        connect(pin_p, capacitor.p);
        connect(capacitor.n, pin_n);
      end IdealBattery;

      model SignalCurrent "Generic current source using the input signal as source current"
        extends Modelica.Electrical.Analog.Interfaces.ConditionalHeatPort(T = 298.15);
        parameter Modelica.Units.SI.Temperature TRef = 298.15 "Reference temperature";
        parameter Modelica.Units.SI.Current IRef = 1 "Reference current at reference irradiance and reference temperature";
        parameter Modelica.Units.SI.Irradiance irradianceRef = 1000 "Reference solar irradiance";
        parameter Modelica.Units.SI.LinearTemperatureCoefficient alphaRef = 0 "Temperature coefficient of reference current at TRref";
        Modelica.Electrical.Analog.Interfaces.PositivePin p;
        Modelica.Electrical.Analog.Interfaces.NegativePin n;
        Modelica.Units.SI.Voltage v "Voltage drop between the two pins (= p.v - n.v)";
        Modelica.Units.SI.Current i "Current flowing from pin p to pin n as input signal";
        Modelica.Blocks.Interfaces.RealInput irradiance(unit = "W/m2") "Irradiance";
      equation
        i = IRef*(irradiance/irradianceRef + alphaRef*(T_heatPort - TRef));
        v = p.v - n.v;
        0 = p.i + n.i;
        i = p.i;
        LossPower = 0;
      end SignalCurrent;
    end Electrical;
  end Sources;

  package Interfaces "Interfaces"
    extends Modelica.Icons.InterfacesPackage;

    partial model PartialComponent "Partial cell or module"
      extends Modelica.Electrical.Analog.Interfaces.TwoPin(v(start = 0));
      extends Modelica.Thermal.HeatTransfer.Interfaces.PartialConditionalHeatPort(T = 298.15);
      parameter Boolean useConstantIrradiance = true "If false, signal input is used" annotation(Evaluate = true, HideResult = true);
      parameter Modelica.Units.SI.Irradiance constantIrradiance = 1000 "Constant solar irradiance, if useConstantIrradiance = true";
      parameter Records.ModuleData moduleData "Module parameters" annotation(choicesAllMatching = true);
      Modelica.Units.SI.Current i = p.i "Current";
      Modelica.Units.SI.Current iGenerating = -i "Negative current (generating)";
      Modelica.Units.SI.Power power = v*i "Power";
      Modelica.Units.SI.Power powerGenerating = v*iGenerating "Negative power consumption (generating)";
      Modelica.Blocks.Interfaces.RealInput variableIrradiance(unit = "W/m2") if not useConstantIrradiance "Solar irradiance";
      Modelica.Blocks.Sources.Constant const(final k = constantIrradiance) if useConstantIrradiance;
    protected
      Modelica.Blocks.Interfaces.RealInput irradiance(unit = "W/m2") "Solar irradiance (either constant or signal input)";
    equation
      connect(irradiance, variableIrradiance);
      connect(const.y, irradiance);
    end PartialComponent;

    partial model PartialCell "Partial cell model"
      extends PhotoVoltaics.Interfaces.PartialComponent;
      parameter Real shadow = 0 "Shadow based on: 0 = full sun, 1 = full shadow";
      PhotoVoltaics.Components.Diodes.Diode2Module diode(final useHeatPort = useHeatPort, final T = T, final TRef = moduleData.TRef);
      PhotoVoltaics.Sources.Electrical.SignalCurrent signalCurrent(final useHeatPort = useHeatPort, final T = T, final TRef = moduleData.TRef);
      Modelica.Blocks.Math.Gain gain(final k = PhotoVoltaics.Functions.limit(1 - shadow, 0, 1));
    equation
      connect(gain.y, signalCurrent.irradiance);
      connect(irradiance, gain.u);
      connect(signalCurrent.p, n);
      connect(p, signalCurrent.n);
      connect(diode.p, signalCurrent.n);
      connect(signalCurrent.heatPort, internalHeatPort);
      connect(diode.n, signalCurrent.p);
      connect(diode.heatPort, internalHeatPort);
    end PartialCell;

    partial model PartialDiode "Diode with one exponential function"
      extends Modelica.Electrical.Analog.Interfaces.OnePort(v(start = 0));
      extends Modelica.Electrical.Analog.Interfaces.ConditionalHeatPort(T = 298.15);
      constant Modelica.Units.SI.Charge Q = 1.6021766208E-19 "Elementary charge of electron";
      parameter Real m = 1 "Ideality factor of diode";
      parameter Modelica.Units.SI.Resistance R = 1E8 "Parallel ohmic resistance";
      parameter Modelica.Units.SI.Temperature TRef = 298.15 "Reference temperature";
      parameter Modelica.Units.SI.Voltage VRef(min = Modelica.Constants.small) = 0.6292 "Reference voltage > 0, i.e. open circuit voltage, at TRef";
      parameter Modelica.Units.SI.Current IRef(min = Modelica.Constants.small) = 8.540 "Reference current > 0, i.e. short circuit current, at TRef";
      parameter Modelica.Units.SI.LinearTemperatureCoefficient alphaI = +0.00053 "Temperature coefficient of reference current at TRef";
      parameter Modelica.Units.SI.LinearTemperatureCoefficient alphaV = -0.00340 "Temperature coefficient of reference voltage at TRef*";
      Modelica.Units.SI.Voltage Vt "Voltage equivalent of temperature (k*T/Q)";
      Modelica.Units.SI.Voltage VRefActual "Reference voltage w.r.t. actual temperature";
      Modelica.Units.SI.Current IRefActual "Reference current w.r.t. actual temperature";
      Modelica.Units.SI.Current Ids "Saturation current";
    equation
      Vt = Modelica.Constants.k*T_heatPort/Q;
      VRefActual = VRef*(1 + alphaV*(T_heatPort - TRef));
      IRefActual = IRef*(1 + alphaI*(T_heatPort - TRef));
      Ids = IRefActual/(exp(VRefActual/m/Vt) - 1);
      LossPower = v*i;
    end PartialDiode;
  end Interfaces;

  package Records "Records"
    extends Modelica.Icons.RecordsPackage;

    record ModuleData "Data of PV module"
      extends Modelica.Icons.Record;
      parameter String moduleName = "Generic";
      parameter Modelica.Units.SI.Temperature TRef = 298.15 "Reference temperature";
      parameter Modelica.Units.SI.Irradiance irradianceRef = 1000 "Reference solar irradiance";
      parameter Modelica.Units.SI.Voltage VocRef(min = Modelica.Constants.small) = 30.2 "Reference open circuit module voltage > 0 at TRref";
      final parameter Modelica.Units.SI.Voltage VocCellRef = VocRef/ns "Reference open circuit cell voltage > 0 at TRref";
      parameter Modelica.Units.SI.Current IscRef(min = Modelica.Constants.small) = 8.54 "Reference short circuit current > 0 at TRref and irradianceRef";
      parameter Modelica.Units.SI.Voltage VmpRef(min = Modelica.Constants.small) = 24.0 "Reference maximum power module voltage > 0 at TRref";
      final parameter Modelica.Units.SI.Voltage VmpCellRef = VmpRef/ns "Reference maximum power cell voltage > 0 at TRref";
      parameter Modelica.Units.SI.Current ImpRef(min = Modelica.Constants.small) = 7.71 "Reference maximum power current > 0 at TRref and irradianceRef";
      parameter Modelica.Units.SI.LinearTemperatureCoefficient alphaIsc = +0.00053 "Temperature coefficient of reference short circuit current at TRref";
      parameter Modelica.Units.SI.LinearTemperatureCoefficient alphaVoc = -0.00340 "Temperature coefficient of reference open circuit module voltage at TRref";
      parameter Integer ns = 1 "Number of series connected cells";
      parameter Integer nb = 1 "Number of bypass diodes per module";
      parameter Modelica.Units.SI.Voltage BvCell = 18 "Breakthrough cell voltage";
      parameter Modelica.Units.SI.Current Ibv = 1 "Breakthrough knee current";
      parameter Real Nbv = 0.74 "Breakthrough emission coefficient";
      final parameter Modelica.Units.SI.Voltage VtCellRef = Modelica.Constants.k*TRef/Q "Reference temperature voltage of cell";
      constant Modelica.Units.SI.Charge Q = 1.6021766208E-19 "Elementary charge of electron";
      annotation(defaultComponentPrefixes = "parameter");
    end ModuleData;

    record SHARP_NU_S5_E3E "SHARP NU monocrystalline SI cell 185W"
      extends ModuleData(final moduleName = "SHARP_NU_S5_E3E", final TRef = 298.15, final irradianceRef = 1000, final VocRef = 30.2, final IscRef = 8.54, final VmpRef = 24.0, final ImpRef = 7.71, final alphaIsc = +0.00053, final alphaVoc = -0.00340, final ns = 48, final nb = 3);
      annotation(defaultComponentPrefixes = "parameter");
    end SHARP_NU_S5_E3E;
  end Records;

  package Icons "Icons"
    extends Modelica.Icons.Package;

    partial model Converter "Converter icon" end Converter;
  end Icons;
  annotation(version = "2.1.0", versionDate = "2025-02-17");
end PhotoVoltaics;

package ModelicaServices "ModelicaServices (OpenModelica implementation) - Models and functions used in the Modelica Standard Library requiring a tool specific implementation"
  extends Modelica.Icons.Package;

  package Machine "Machine dependent constants"
    extends Modelica.Icons.Package;
    final constant Real eps = 2.2204460492503131e-016 "The difference between 1 and the least value greater than 1 that is representable in the given floating point type";
    final constant Real small = 2.2250738585072014e-308 "Minimum normalized positive floating-point number";
    final constant Real inf = 1e60 "Maximum representable finite floating-point number";
    final constant Integer Integer_inf = OpenModelica.Internal.Architecture.integerMax() "Biggest Integer number such that Integer_inf and -Integer_inf are representable on the machine";
  end Machine;
  annotation(version = "4.1.0", versionDate = "2025-05-23", dateModified = "2025-05-23 15:00:00Z");
end ModelicaServices;

package Modelica "Modelica Standard Library"
  extends Modelica.Icons.Package;

  package Blocks "Library of basic input/output control blocks (continuous, discrete, logical, table blocks)"
    extends Modelica.Icons.Package;
    import Modelica.Units.SI;

    package Continuous "Library of continuous control blocks with internal states"
      import Modelica.Blocks.Interfaces;
      extends Modelica.Icons.Package;

      block Integrator "Output the integral of the input signal with optional reset"
        import Modelica.Blocks.Types.Init;
        parameter Real k = 1 "Integrator gain";
        parameter Boolean use_reset = false "= true, if reset port enabled" annotation(Evaluate = true, HideResult = true);
        parameter Boolean use_set = false "= true, if set port enabled and used as reinitialization value when reset" annotation(Evaluate = true, HideResult = true);
        parameter Init initType = Init.InitialState "Type of initialization (1: no init, 2: steady state, 3,4: initial output)" annotation(Evaluate = true);
        parameter Real y_start = 0 "Initial or guess value of output (= state)";
        extends Interfaces.SISO;
        Modelica.Blocks.Interfaces.BooleanInput reset if use_reset "Optional connector of reset signal";
        Modelica.Blocks.Interfaces.RealInput set if use_reset and use_set "Optional connector of set signal";
      protected
        Modelica.Blocks.Interfaces.BooleanOutput local_reset annotation(HideResult = true);
        Modelica.Blocks.Interfaces.RealOutput local_set annotation(HideResult = true);
      initial equation
        if initType == Init.SteadyState then
          der(y) = 0;
        elseif initType == Init.InitialState or initType == Init.InitialOutput then
          y = y_start;
        end if;
      equation
        if use_reset then
          connect(reset, local_reset);
          if use_set then
            connect(set, local_set);
          else
            local_set = y_start;
          end if;
          when local_reset then
            reinit(y, local_set);
          end when;
        else
          local_reset = false;
          local_set = 0;
        end if;
        der(y) = k*u;
      end Integrator;
    end Continuous;

    package Interfaces "Library of connectors and partial models for input/output blocks"
      extends Modelica.Icons.InterfacesPackage;
      connector RealInput = input Real "'input Real' as connector";
      connector RealOutput = output Real "'output Real' as connector";
      connector BooleanInput = input Boolean "'input Boolean' as connector";
      connector BooleanOutput = output Boolean "'output Boolean' as connector";

      partial block SO "Single Output continuous control block"
        extends Modelica.Blocks.Icons.Block;
        RealOutput y "Connector of Real output signal";
      end SO;

      partial block SISO "Single Input Single Output continuous control block"
        extends Modelica.Blocks.Icons.Block;
        RealInput u "Connector of Real input signal";
        RealOutput y "Connector of Real output signal";
      end SISO;

      partial block SI2SO "2 Single Input / 1 Single Output continuous control block"
        extends Modelica.Blocks.Icons.Block;
        RealInput u1 "Connector of Real input signal 1";
        RealInput u2 "Connector of Real input signal 2";
        RealOutput y "Connector of Real output signal";
      end SI2SO;
    end Interfaces;

    package Math "Library of Real mathematical functions as input/output blocks"
      import Modelica.Blocks.Interfaces;
      extends Modelica.Icons.Package;

      block Gain "Output the product of a gain value with the input signal"
        parameter Real k(start = 1) "Gain value multiplied with input signal";
        Interfaces.RealInput u "Input signal connector";
        Interfaces.RealOutput y "Output signal connector";
      equation
        y = k*u;
      end Gain;

      block Feedback "Output difference between commanded and feedback input"
        Interfaces.RealInput u1 "Commanded input";
        Interfaces.RealInput u2 "Feedback input";
        Interfaces.RealOutput y;
      equation
        y = u1 - u2;
      end Feedback;

      block Product "Output product of the two inputs"
        extends Interfaces.SI2SO;
      equation
        y = u1*u2;
      end Product;
    end Math;

    package Sources "Library of signal source blocks generating Real, Integer and Boolean signals"
      import Modelica.Blocks.Interfaces;
      extends Modelica.Icons.SourcesPackage;

      block Constant "Generate constant signal of type Real"
        parameter Real k(start = 1) "Constant output value";
        extends Interfaces.SO;
      equation
        y = k;
      end Constant;
    end Sources;

    package Types "Library of constants, external objects and types with choices, especially to build menus"
      extends Modelica.Icons.TypesPackage;
      type Init = enumeration(NoInit "No initialization (start values are used as guess values with fixed=false)", SteadyState "Steady state initialization (derivatives of states are zero)", InitialState "Initialization with initial states", InitialOutput "Initialization with initial outputs (and steady state of the states if possible)") "Enumeration defining initialization of a block" annotation(Evaluate = true);
    end Types;

    package Icons "Icons for Blocks"
      extends Modelica.Icons.IconsPackage;

      partial block Block "Basic graphical layout of input/output block" end Block;
    end Icons;
  end Blocks;

  package Electrical "Library of electrical models (analog, digital, machines, polyphase)"
    extends Modelica.Icons.Package;
    import Modelica.Units.SI;

    package Analog "Library for analog electrical models"
      extends Modelica.Icons.Package;

      package Basic "Basic electrical components"
        extends Modelica.Icons.Package;

        model Ground "Ground node"
          Interfaces.Pin p;
        equation
          p.v = 0;
        end Ground;

        model Capacitor "Ideal linear electrical capacitor"
          extends Interfaces.OnePort(v(start = 0));
          parameter SI.Capacitance C(start = 1) "Capacitance";
        equation
          i = C*der(v);
        end Capacitor;
      end Basic;

      package Interfaces "Connectors and partial models for Analog electrical components"
        extends Modelica.Icons.InterfacesPackage;

        connector Pin "Pin of an electrical component"
          SI.ElectricPotential v "Potential at the pin" annotation(unassignedMessage = "An electrical potential cannot be uniquely calculated.
        The reason could be that
        - a ground object is missing (Modelica.Electrical.Analog.Basic.Ground)
          to define the zero potential of the electrical circuit, or
        - a connector of an electrical component is not connected.");
          flow SI.Current i "Current flowing into the pin" annotation(unassignedMessage = "An electrical current cannot be uniquely calculated.
        The reason could be that
        - a ground object is missing (Modelica.Electrical.Analog.Basic.Ground)
          to define the zero potential of the electrical circuit, or
        - a connector of an electrical component is not connected.");
        end Pin;

        connector PositivePin "Positive pin of an electrical component"
          SI.ElectricPotential v "Potential at the pin" annotation(unassignedMessage = "An electrical potential cannot be uniquely calculated.
        The reason could be that
        - a ground object is missing (Modelica.Electrical.Analog.Basic.Ground)
          to define the zero potential of the electrical circuit, or
        - a connector of an electrical component is not connected.");
          flow SI.Current i "Current flowing into the pin" annotation(unassignedMessage = "An electrical current cannot be uniquely calculated.
        The reason could be that
        - a ground object is missing (Modelica.Electrical.Analog.Basic.Ground)
          to define the zero potential of the electrical circuit, or
        - a connector of an electrical component is not connected.");
        end PositivePin;

        connector NegativePin "Negative pin of an electrical component"
          SI.ElectricPotential v "Potential at the pin" annotation(unassignedMessage = "An electrical potential cannot be uniquely calculated.
        The reason could be that
        - a ground object is missing (Modelica.Electrical.Analog.Basic.Ground)
          to define the zero potential of the electrical circuit, or
        - a connector of an electrical component is not connected.");
          flow SI.Current i "Current flowing into the pin" annotation(unassignedMessage = "An electrical current cannot be uniquely calculated.
        The reason could be that
        - a ground object is missing (Modelica.Electrical.Analog.Basic.Ground)
          to define the zero potential of the electrical circuit, or
        - a connector of an electrical component is not connected.");
        end NegativePin;

        partial model TwoPin "Component with two electrical pins"
          SI.Voltage v "Voltage drop of the two pins (= p.v - n.v)";
          PositivePin p "Positive electrical pin";
          NegativePin n "Negative electrical pin";
        equation
          v = p.v - n.v;
        end TwoPin;

        partial model OnePort "Component with two electrical pins p and n and current i from p to n"
          extends TwoPin;
          SI.Current i "Current flowing from pin p to pin n";
        equation
          0 = p.i + n.i;
          i = p.i;
        end OnePort;

        partial model ConditionalHeatPort "Partial model to include a conditional HeatPort in order to describe the power loss via a thermal network"
          parameter Boolean useHeatPort = false "= true, if heatPort is enabled" annotation(Evaluate = true, HideResult = true);
          parameter SI.Temperature T = 293.15 "Fixed device temperature if useHeatPort = false";
          Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a heatPort(final T = T_heatPort, final Q_flow = -LossPower) if useHeatPort "Conditional heat port";
          SI.Power LossPower "Loss power leaving component via heatPort";
          SI.Temperature T_heatPort "Temperature of heatPort";
        equation
          if not useHeatPort then
            T_heatPort = T;
          end if;
        end ConditionalHeatPort;
      end Interfaces;

      package Sensors "Potential, voltage, current, and power sensors"
        extends Modelica.Icons.SensorsPackage;

        model VoltageSensor "Sensor to measure the voltage between two pins"
          extends Modelica.Icons.RoundSensor;
          Interfaces.PositivePin p "Positive pin";
          Interfaces.NegativePin n "Negative pin";
          Modelica.Blocks.Interfaces.RealOutput v(unit = "V") "Voltage between pin p and n (= p.v - n.v) as output signal";
        equation
          p.i = 0;
          n.i = 0;
          v = p.v - n.v;
        end VoltageSensor;

        model CurrentSensor "Sensor to measure the current in a branch"
          extends Modelica.Icons.RoundSensor;
          Interfaces.PositivePin p "Positive pin";
          Interfaces.NegativePin n "Negative pin";
          Modelica.Blocks.Interfaces.RealOutput i(unit = "A") "Current in the branch from p to n as output signal";
        equation
          p.v = n.v;
          p.i = i;
          n.i = -i;
        end CurrentSensor;

        model PowerSensor "Sensor to measure the power"
          extends Modelica.Icons.RoundSensor;
          Modelica.Electrical.Analog.Interfaces.PositivePin pc "Positive pin, current path";
          Modelica.Electrical.Analog.Interfaces.NegativePin nc "Negative pin, current path";
          Modelica.Electrical.Analog.Interfaces.PositivePin pv "Positive pin, voltage path";
          Modelica.Electrical.Analog.Interfaces.NegativePin nv "Negative pin, voltage path";
          Modelica.Blocks.Interfaces.RealOutput power(unit = "W") "Instantaneous power as output signal";
          Modelica.Electrical.Analog.Sensors.VoltageSensor voltageSensor;
          Modelica.Electrical.Analog.Sensors.CurrentSensor currentSensor;
          Modelica.Blocks.Math.Product product;
        equation
          connect(pv, voltageSensor.p);
          connect(voltageSensor.n, nv);
          connect(pc, currentSensor.p);
          connect(currentSensor.n, nc);
          connect(currentSensor.i, product.u2);
          connect(voltageSensor.v, product.u1);
          connect(product.y, power);
        end PowerSensor;
      end Sensors;

      package Sources "Time-dependent and controlled voltage and current sources"
        extends Modelica.Icons.SourcesPackage;

        model SignalVoltage "Generic voltage source using the input signal as source voltage"
          extends Modelica.Electrical.Analog.Icons.VoltageSource;
          Interfaces.PositivePin p;
          Interfaces.NegativePin n;
          Modelica.Blocks.Interfaces.RealInput v(unit = "V") "Voltage between pin p and n (= p.v - n.v) as input signal";
          SI.Current i "Current flowing from pin p to pin n";
        equation
          v = p.v - n.v;
          0 = p.i + n.i;
          i = p.i;
        end SignalVoltage;

        model SignalCurrent "Generic current source using the input signal as source current"
          extends Modelica.Electrical.Analog.Icons.CurrentSource;
          Interfaces.PositivePin p;
          Interfaces.NegativePin n;
          Modelica.Blocks.Interfaces.RealInput i(unit = "A") "Current flowing from pin p to pin n as input signal";
          SI.Voltage v "Voltage drop between the two pins (= p.v - n.v)";
        equation
          v = p.v - n.v;
          0 = p.i + n.i;
          i = p.i;
        end SignalCurrent;
      end Sources;

      package Icons "Icons for analog electrical models"
        extends Modelica.Icons.IconsPackage;

        partial model VoltageSource "Icon for voltage sources" end VoltageSource;

        partial model CurrentSource "Icon for current sources" end CurrentSource;
      end Icons;
    end Analog;

    package PowerConverters "Rectifiers, Inverters, DC/DC and AC/AC converters"
      extends Modelica.Icons.Package;

      package Interfaces "Interfaces"
        extends Modelica.Icons.InterfacesPackage;

        package DCDC "DC to DC converter interfaces"
          extends Modelica.Icons.InterfacesPackage;

          partial model DCtwoPin1 "Positive and negative pins of side 1"
            Modelica.Electrical.Analog.Interfaces.PositivePin dc_p1 "Positive DC input";
            Modelica.Electrical.Analog.Interfaces.NegativePin dc_n1 "Negative DC input";
            SI.Voltage vDC1 = dc_p1.v - dc_n1.v "DC voltage side 1";
            SI.Current iDC1 = dc_p1.i "DC current side 1";
            SI.Power powerDC1 = vDC1*iDC1 "DC power side 1";
          end DCtwoPin1;

          partial model DCtwoPin2 "Positive and negative pins of side 2"
            Modelica.Electrical.Analog.Interfaces.PositivePin dc_p2 "Positive DC output";
            Modelica.Electrical.Analog.Interfaces.NegativePin dc_n2 "Negative DC output";
            SI.Voltage vDC2 = dc_p2.v - dc_n2.v "DC voltages side 2";
            SI.Current iDC2 = dc_p2.i "DC current side 2";
            SI.Power powerDC2 = vDC2*iDC2 "DC power side 2";
          end DCtwoPin2;
        end DCDC;
      end Interfaces;
    end PowerConverters;
  end Electrical;

  package Thermal "Library of thermal system components to model heat transfer and simple thermo-fluid pipe flow"
    extends Modelica.Icons.Package;
    import Modelica.Units.SI;

    package HeatTransfer "Library of 1-dimensional heat transfer with lumped elements"
      extends Modelica.Icons.Package;

      package Sources "Thermal sources"
        extends Modelica.Icons.SourcesPackage;

        model FixedTemperature "Fixed temperature boundary condition in Kelvin"
          parameter SI.Temperature T "Fixed temperature at port";
          Interfaces.HeatPort_b port;
        equation
          port.T = T;
        end FixedTemperature;
      end Sources;

      package Interfaces "Connectors and partial models"
        extends Modelica.Icons.InterfacesPackage;

        partial connector HeatPort "Thermal port for 1-dim. heat transfer"
          SI.Temperature T "Port temperature";
          flow SI.HeatFlowRate Q_flow "Heat flow rate (positive if flowing from outside into the component)";
        end HeatPort;

        connector HeatPort_a "Thermal port for 1-dim. heat transfer (filled rectangular icon)"
          extends HeatPort;
        end HeatPort_a;

        connector HeatPort_b "Thermal port for 1-dim. heat transfer (unfilled rectangular icon)"
          extends HeatPort;
        end HeatPort_b;

        partial model PartialConditionalHeatPort "Partial model to include a conditional HeatPort in order to dissipate losses, used for graphical modeling, i.e., for building models by drag-and-drop"
          parameter Boolean useHeatPort = false "= true, if HeatPort is enabled" annotation(Evaluate = true, HideResult = true);
          parameter SI.Temperature T = 293.15 "Fixed device temperature if useHeatPort = false";
          HeatTransfer.Interfaces.HeatPort_a heatPort if useHeatPort "Optional port to which dissipated losses are transported in form of heat";
          HeatTransfer.Sources.FixedTemperature fixedTemperature(final T = T) if not useHeatPort;
        protected
          HeatPort_a internalHeatPort;
        equation
          connect(heatPort, internalHeatPort);
          connect(fixedTemperature.port, internalHeatPort);
        end PartialConditionalHeatPort;
      end Interfaces;
    end HeatTransfer;
  end Thermal;

  package Math "Library of mathematical functions (e.g., sin, cos) and of functions operating on vectors and matrices"
    extends Modelica.Icons.Package;

    package Icons "Icons for Math"
      extends Modelica.Icons.IconsPackage;

      partial function AxisCenter "Basic icon for mathematical function with y-axis in the center" end AxisCenter;
    end Icons;

    function asin "Inverse sine (-1 <= u <= 1)"
      extends Modelica.Math.Icons.AxisCenter;
      input Real u "Independent variable";
      output Modelica.Units.SI.Angle y "Dependent variable y=asin(u)";
    algorithm
      y := .asin(u);
      annotation(Inline = true);
    end asin;

    function exp "Exponential, base e"
      extends Modelica.Math.Icons.AxisCenter;
      input Real u "Independent variable";
      output Real y "Dependent variable y=exp(u)";
    algorithm
      y := .exp(u);
      annotation(Inline = true);
    end exp;
  end Math;

  package Constants "Library of mathematical constants and constants of nature (e.g., pi, eps, R, sigma)"
    extends Modelica.Icons.Package;
    import Modelica.Units.SI;
    import Modelica.Units.NonSI;
    final constant Real pi = 2*Modelica.Math.asin(1.0);
    final constant Real small = ModelicaServices.Machine.small "Minimum normalized positive floating-point number";
    final constant SI.Velocity c = 299792458 "Speed of light in vacuum";
    final constant SI.ElectricCharge q = 1.602176634e-19 "Elementary charge";
    final constant Real h(final unit = "J.s") = 6.62607015e-34 "Planck constant";
    final constant Real k(final unit = "J/K") = 1.380649e-23 "Boltzmann constant";
    final constant Real N_A(final unit = "1/mol") = 6.02214076e23 "Avogadro constant";
    final constant SI.Permeability mu_0 = 1.25663706212e-6 "Magnetic constant";
  end Constants;

  package Icons "Library of icons"
    extends Icons.Package;

    partial package ExamplesPackage "Icon for packages containing runnable examples"
      extends Modelica.Icons.Package;
    end ExamplesPackage;

    partial model Example "Icon for runnable examples" end Example;

    partial package Package "Icon for standard packages" end Package;

    partial package InterfacesPackage "Icon for packages containing interfaces"
      extends Modelica.Icons.Package;
    end InterfacesPackage;

    partial package SourcesPackage "Icon for packages containing sources"
      extends Modelica.Icons.Package;
    end SourcesPackage;

    partial package SensorsPackage "Icon for packages containing sensors"
      extends Modelica.Icons.Package;
    end SensorsPackage;

    partial package TypesPackage "Icon for packages containing type definitions"
      extends Modelica.Icons.Package;
    end TypesPackage;

    partial package IconsPackage "Icon for packages containing icons"
      extends Modelica.Icons.Package;
    end IconsPackage;

    partial package RecordsPackage "Icon for package containing records"
      extends Modelica.Icons.Package;
    end RecordsPackage;

    partial class RoundSensor "Icon representing a round measurement device" end RoundSensor;

    partial function Function "Icon for functions" end Function;

    partial record Record "Icon for records" end Record;
  end Icons;

  package Units "Library of type and unit definitions"
    extends Modelica.Icons.Package;

    package SI "Library of SI unit definitions"
      extends Modelica.Icons.Package;
      type Angle = Real(final quantity = "Angle", final unit = "rad", displayUnit = "deg");
      type Time = Real(final quantity = "Time", final unit = "s");
      type Velocity = Real(final quantity = "Velocity", final unit = "m/s");
      type Acceleration = Real(final quantity = "Acceleration", final unit = "m/s2");
      type Energy = Real(final quantity = "Energy", final unit = "J");
      type Power = Real(final quantity = "Power", final unit = "W");
      type ThermodynamicTemperature = Real(final quantity = "ThermodynamicTemperature", final unit = "K", min = 0.0, start = 288.15, nominal = 300, displayUnit = "degC") "Absolute temperature (use type TemperatureDifference for relative temperatures)" annotation(absoluteValue = true);
      type Temperature = ThermodynamicTemperature;
      type LinearTemperatureCoefficient = Real(final quantity = "LinearTemperatureCoefficient", final unit = "1/K");
      type HeatFlowRate = Real(final quantity = "Power", final unit = "W");
      type ElectricCurrent = Real(final quantity = "ElectricCurrent", final unit = "A");
      type Current = ElectricCurrent;
      type ElectricCharge = Real(final quantity = "ElectricCharge", final unit = "C");
      type Charge = ElectricCharge;
      type ElectricPotential = Real(final quantity = "ElectricPotential", final unit = "V");
      type Voltage = ElectricPotential;
      type Capacitance = Real(final quantity = "Capacitance", final unit = "F", min = 0);
      type Permeability = Real(final quantity = "Permeability", final unit = "V.s/(A.m)");
      type Resistance = Real(final quantity = "Resistance", final unit = "Ohm");
      type Irradiance = Real(final quantity = "Irradiance", final unit = "W/m2");
      type FaradayConstant = Real(final quantity = "FaradayConstant", final unit = "C/mol");
    end SI;

    package NonSI "Type definitions of non SI and other units"
      extends Modelica.Icons.Package;
      type Temperature_degC = Real(final quantity = "ThermodynamicTemperature", final unit = "degC") "Absolute temperature in degree Celsius (for relative temperature use Modelica.Units.SI.TemperatureDifference)" annotation(absoluteValue = true);
      type Time_day = Real(final quantity = "Time", final unit = "d") "Time in days";
      type Time_hour = Real(final quantity = "Time", final unit = "h") "Time in hours";
    end NonSI;
  end Units;
  annotation(version = "4.1.0", versionDate = "2025-05-23", dateModified = "2025-05-23 15:00:00Z");
end Modelica;

model SimpleModuleMPDC_total  "Simple module supplies DC grid with maximum power tracker"
  extends PhotoVoltaics.Examples.SimpleModuleMPDC;
 annotation(experiment(StopTime = 86400, Interval = 1, Tolerance = 1e-06, StartTime = 0), __OpenModelica_simulationFlags(jacobian = "coloredNumerical", nls = "newton", s = "dassl", lv = "LOG_STATS"));
end SimpleModuleMPDC_total;
