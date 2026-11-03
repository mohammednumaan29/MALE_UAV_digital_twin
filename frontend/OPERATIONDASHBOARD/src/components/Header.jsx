import React, { useEffect, useMemo, useState } from 'react';

import {
  Menu,
  Bell,
  Sun,
  Wind,
  Cloud,
  ChevronDown,
} from 'lucide-react';


/* ============================================================
   FLIGHT CONFIGURATION
   ============================================================ */

const FLIGHT_CONFIG = {
  uavId: 'UAV-2026-045',
  phase: 'Cruise',
  altitude: '5,200 ft',
  groundSpeed: '120 kt',

  /*
   * Initial mission time remaining.
   *
   * 02:18:37
   */
  initialRemainingSeconds:
    (2 * 60 * 60) +
    (18 * 60) +
    37,
};


/* ============================================================
   WEATHER
   ============================================================ */

const WEATHER = {
  temperature: '32°C',
  wind: '7 kt',
  condition: 'Clear',
};


/* ============================================================
   TIMEZONE
   ============================================================ */

/*
 * Dashboard timezone.
 *
 * India Standard Time:
 *
 * UTC + 05:30
 *
 * Using Intl with an explicit timezone is safer than manually
 * adding 5 hours 30 minutes because it handles the date correctly.
 */

const DASHBOARD_TIMEZONE = 'Asia/Kolkata';


/* ============================================================
   HELPERS
   ============================================================ */

function pad(value) {
  return String(value).padStart(2, '0');
}


/* ============================================================
   FORMAT LOCAL DATE / TIME
   ============================================================ */

function formatDashboardDateTime(date) {

  const parts = new Intl.DateTimeFormat(
    'en-GB',
    {
      timeZone: DASHBOARD_TIMEZONE,

      day: '2-digit',
      month: 'short',
      year: 'numeric',

      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',

      hour12: false,
    }
  ).formatToParts(date);


  const values = {};

  parts.forEach((part) => {

    if (part.type !== 'literal') {
      values[part.type] = part.value;
    }

  });


  return (
    `${values.day} ` +
    `${values.month} ` +
    `${values.year} ` +
    `${values.hour}:` +
    `${values.minute}:` +
    `${values.second} ` +
    `(IST)`
  );
}


/* ============================================================
   FORMAT COUNTDOWN
   ============================================================ */

function formatCountdown(totalSeconds) {

  const safeSeconds =
    Math.max(0, Math.floor(totalSeconds));


  const hours =
    Math.floor(safeSeconds / 3600);


  const minutes =
    Math.floor(
      (safeSeconds % 3600) / 60
    );


  const seconds =
    safeSeconds % 60;


  return (
    `${pad(hours)}:` +
    `${pad(minutes)}:` +
    `${pad(seconds)}`
  );
}


/* ============================================================
   HEADER
   ============================================================ */

export default function Header({
  onMenuClick,
  notifications = 2,
  userInitials = 'AK',
}) {

  /* ==========================================================
     REAL SYSTEM TIME
     ========================================================== */

  const [currentTime, setCurrentTime] = useState(
    () => new Date()
  );


  /* ==========================================================
     MISSION COUNTDOWN
     ========================================================== */

  const [remainingSeconds, setRemainingSeconds] =
    useState(
      FLIGHT_CONFIG.initialRemainingSeconds
    );


  /* ==========================================================
     UPDATE REAL CLOCK
     ========================================================== */

  useEffect(() => {

    /*
     * Update immediately and then every second.
     */

    const updateClock = () => {

      setCurrentTime(new Date());

    };


    updateClock();


    const timer = setInterval(
      updateClock,
      1000
    );


    return () => {

      clearInterval(timer);

    };

  }, []);


  /* ==========================================================
     UPDATE MISSION COUNTDOWN
     ========================================================== */

  useEffect(() => {

    const timer = setInterval(() => {

      setRemainingSeconds(
        (previous) => {

          if (previous <= 0) {
            return 0;
          }

          return previous - 1;

        }
      );

    }, 1000);


    return () => {

      clearInterval(timer);

    };

  }, []);


  /* ==========================================================
     FORMATTED TIME
     ========================================================== */

  const formattedDateTime = useMemo(
    () => formatDashboardDateTime(currentTime),
    [currentTime]
  );


  /* ==========================================================
     FORMATTED COUNTDOWN
     ========================================================== */

  const formattedCountdown = useMemo(
    () =>
      formatCountdown(
        remainingSeconds
      ),
    [remainingSeconds]
  );


  /* ==========================================================
     HEADER
     ========================================================== */

  return (

    <header
      className="
        relative
        z-50
        h-[72px]
        w-full
        shrink-0
        overflow-hidden
        border-b
        border-slate-200
        bg-white
      "
    >

      {/* ======================================================
          BACKGROUND
          ====================================================== */}

      <div
        className="
          pointer-events-none
          absolute
          inset-0
          overflow-hidden
        "
      >

        <div
          className="
            absolute
            inset-0
            bg-gradient-to-r
            from-white
            via-slate-50
            to-slate-100
          "
        />

        <div
          className="
            absolute
            right-[18%]
            top-0
            h-full
            w-[450px]
            bg-gradient-to-r
            from-transparent
            via-slate-100/50
            to-transparent
          "
        />

      </div>


      {/* ======================================================
          HEADER CONTENT
          ====================================================== */}

      <div
        className="
          relative
          flex
          h-full
          w-full
          items-center
          px-5
        "
      >


        {/* ====================================================
            LEFT
            ==================================================== */}

        <div
          className="
            flex
            min-w-0
            shrink-0
            items-center
          "
        >

          {/* Menu */}

          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Toggle dashboard menu"
            className="
              mr-4
              flex
              h-8
              w-8
              shrink-0
              items-center
              justify-center
              rounded-lg
              text-slate-600
              transition
              hover:bg-slate-100
              hover:text-slate-900
            "
          >

            <Menu
              className="
                h-5
                w-5
              "
            />

          </button>


          {/* System title */}

          <div
            className="
              min-w-0
            "
          >

            <div
              className="
                flex
                items-center
                gap-2
              "
            >

              <h1
                className="
                  whitespace-nowrap
                  text-[18px]
                  font-bold
                  leading-[21px]
                  tracking-[-0.02em]
                  text-slate-900
                "
              >
                Engine Monitoring System
              </h1>


              <span
                className="
                  inline-flex
                  h-[20px]
                  shrink-0
                  items-center
                  rounded
                  border
                  border-blue-200
                  bg-blue-50
                  px-1.5
                  text-[9px]
                  font-semibold
                  leading-none
                  text-blue-700
                "
              >
                ROTAX 914
              </span>

            </div>


            <p
              className="
                mt-[2px]
                whitespace-nowrap
                text-[10px]
                font-medium
                leading-[13px]
                text-slate-500
              "
            >

              Real-Time Monitoring

              <span
                className="
                  mx-1
                  text-slate-300
                "
              >
                |
              </span>

              Predict

              <span
                className="
                  mx-1
                  text-slate-300
                "
              >
                |
              </span>

              Ensure Safe Operations

            </p>

          </div>

        </div>



        {/* ====================================================
            CENTER FLIGHT INFORMATION
            ==================================================== */}

        <div
          className="
            absolute
            left-1/2
            hidden
            -translate-x-1/2
            xl:flex
          "
        >

          <div
            className="
              flex
              h-[32px]
              items-center
              whitespace-nowrap
              rounded-full
              border
              border-slate-200
              bg-white
              px-3
              shadow-sm
            "
          >

            {/* UAV */}

            <span
              className="
                text-[11px]
                font-semibold
                text-slate-700
              "
            >
              {FLIGHT_CONFIG.uavId}
            </span>


            <span className="mx-2 text-slate-300">
              |
            </span>


            {/* Phase */}

            <span
              className="
                text-[11px]
                font-medium
                text-slate-600
              "
            >
              {FLIGHT_CONFIG.phase}
            </span>


            <span className="mx-2 text-slate-300">
              |
            </span>


            {/* Altitude */}

            <span
              className="
                text-[11px]
                font-medium
                text-slate-600
              "
            >
              Alt {FLIGHT_CONFIG.altitude}
            </span>


            <span className="mx-2 text-slate-300">
              |
            </span>


            {/* Ground speed */}

            <span
              className="
                text-[11px]
                font-medium
                text-slate-600
              "
            >
              GS {FLIGHT_CONFIG.groundSpeed}
            </span>


            <span className="mx-2 text-slate-300">
              |
            </span>


            {/* Countdown */}

            <span
              className="
                font-mono
                text-[11px]
                font-bold
                tabular-nums
                text-orange-600
              "
            >
              {formattedCountdown} left
            </span>

          </div>

        </div>



        {/* ====================================================
            RIGHT SIDE
            ==================================================== */}

        <div
          className="
            ml-auto
            flex
            shrink-0
            items-center
            gap-4
          "
        >


          {/* ==================================================
              LIVE STATUS
              ================================================== */}

          <div
            className="
              flex
              h-[28px]
              items-center
              gap-1.5
              rounded-full
              border
              border-emerald-200
              bg-emerald-50
              px-2.5
            "
          >

            <span
              className="
                relative
                flex
                h-2
                w-2
              "
            >

              <span
                className="
                  absolute
                  h-full
                  w-full
                  animate-ping
                  rounded-full
                  bg-emerald-400
                  opacity-50
                "
              />

              <span
                className="
                  relative
                  h-2
                  w-2
                  rounded-full
                  bg-emerald-500
                "
              />

            </span>


            <span
              className="
                text-[11px]
                font-semibold
                leading-none
                text-emerald-700
              "
            >
              Live
            </span>

          </div>



          {/* ==================================================
              REAL INDIA DATE / TIME
              ================================================== */}

          <div
            className="
              hidden
              whitespace-nowrap
              font-mono
              text-[10px]
              font-medium
              leading-none
              tabular-nums
              text-slate-600
              2xl:block
            "
          >

            {formattedDateTime}

          </div>



          {/* ==================================================
              WEATHER
              ================================================== */}

          <div
            className="
              hidden
              items-center
              gap-3
              lg:flex
            "
          >

            {/* Temperature */}

            <div
              className="
                flex
                items-center
                gap-1.5
                whitespace-nowrap
                text-[10px]
                font-medium
                text-slate-600
              "
            >

              <Sun
                className="
                  h-3.5
                  w-3.5
                  text-orange-500
                "
              />

              <span>
                {WEATHER.temperature}
              </span>

            </div>


            {/* Wind */}

            <div
              className="
                flex
                items-center
                gap-1.5
                whitespace-nowrap
                text-[10px]
                font-medium
                text-slate-600
              "
            >

              <Wind
                className="
                  h-3.5
                  w-3.5
                  text-sky-500
                "
              />

              <span>
                {WEATHER.wind}
              </span>

            </div>


            {/* Weather condition */}

            <div
              className="
                flex
                items-center
                gap-1.5
                whitespace-nowrap
                text-[10px]
                font-medium
                text-slate-600
              "
            >

              <Cloud
                className="
                  h-3.5
                  w-3.5
                  text-sky-500
                "
              />

              <span>
                {WEATHER.condition}
              </span>

            </div>

          </div>



          {/* ==================================================
              NOTIFICATIONS
              ================================================== */}

          <button
            type="button"
            aria-label={`${notifications} notifications`}
            className="
              relative
              flex
              h-8
              w-8
              shrink-0
              items-center
              justify-center
              rounded-lg
              text-slate-500
              transition
              hover:bg-slate-100
              hover:text-slate-800
            "
          >

            <Bell
              className="
                h-[17px]
                w-[17px]
              "
            />


            {notifications > 0 && (

              <span
                className="
                  absolute
                  right-0
                  top-0
                  flex
                  h-[14px]
                  min-w-[14px]
                  items-center
                  justify-center
                  rounded-full
                  border-2
                  border-white
                  bg-red-500
                  px-0.5
                  text-[7px]
                  font-bold
                  leading-none
                  text-white
                "
              >
                {notifications}
              </span>

            )}

          </button>



          {/* ==================================================
              USER
              ================================================== */}

          <button
            type="button"
            aria-label="Open user menu"
            className="
              flex
              shrink-0
              items-center
              gap-1.5
              rounded-full
              transition
              hover:opacity-80
            "
          >

            <span
              className="
                flex
                h-[30px]
                w-[30px]
                items-center
                justify-center
                rounded-full
                bg-blue-600
                text-[10px]
                font-bold
                leading-none
                text-white
                shadow-sm
              "
            >
              {userInitials}
            </span>


            <ChevronDown
              className="
                hidden
                h-3.5
                w-3.5
                text-slate-400
                xl:block
              "
            />

          </button>

        </div>

      </div>

    </header>
  );
}