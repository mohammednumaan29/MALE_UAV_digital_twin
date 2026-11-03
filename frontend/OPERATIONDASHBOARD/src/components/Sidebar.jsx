import React from 'react';

import {
  LayoutDashboard,
  Activity,
  ShieldAlert,
  Plane,
  Box,
  FileText,
  Menu,
  ShieldCheck,
} from 'lucide-react';


/* ============================================================
   NAVIGATION ITEMS
   ============================================================ */

const navigationItems = [
  {
    id: 'overview',
    label: 'Overview',
    icon: LayoutDashboard,
  },
  {
    id: 'telemetry',
    label: 'Telemetry',
    icon: Activity,
  },
  {
    id: 'diagnostics',
    label: 'Diagnostics',
    icon: ShieldAlert,
  },
  {
    id: 'mission',
    label: 'Mission',
    icon: Plane,
  },
  {
    id: 'simulation',
    label: 'Simulation',
    icon: Box,
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: FileText,
  },
];


/* ============================================================
   SIDEBAR
   ============================================================ */

export default function Sidebar({
  activeView = 'overview',
  onNavigate,
  collapsed = false,
  onToggle,
}) {

  return (
    <aside
      className={`
        fixed
        left-0
        top-0
        z-40
        flex
        h-screen
        flex-col
        border-r
        border-slate-200
        bg-white
        transition-all
        duration-200
        ${collapsed ? 'w-[68px]' : 'w-[220px]'}
      `}
    >

      {/* ======================================================
          TOP
          ====================================================== */}

      <div
        className={`
          flex
          h-[72px]
          shrink-0
          items-center
          border-b
          border-slate-100
          ${collapsed ? 'justify-center px-2' : 'px-4'}
        `}
      >

        {/* Logo */}

        <div
          className={`
            flex
            min-w-0
            items-center
            ${collapsed ? 'justify-center' : 'gap-2.5'}
          `}
        >

          <div
            className="
              flex
              h-9
              w-9
              shrink-0
              items-center
              justify-center
              rounded-lg
              bg-blue-600
              text-white
            "
          >

            <Activity className="h-5 w-5" />

          </div>


          {!collapsed && (

            <div className="min-w-0">

              <div className="
                truncate
                text-[13px]
                font-bold
                leading-4
                text-slate-900
              ">
                Engine Monitor
              </div>

              <div className="
                mt-0.5
                truncate
                text-[9px]
                font-medium
                leading-3
                text-slate-400
              ">
                ROTAX 914
              </div>

            </div>

          )}

        </div>


        {/* Collapse button */}

        {!collapsed && (

          <button
            type="button"
            onClick={onToggle}
            aria-label="Collapse navigation"
            className="
              ml-auto
              flex
              h-7
              w-7
              shrink-0
              items-center
              justify-center
              rounded-md
              text-slate-400
              transition
              hover:bg-slate-100
              hover:text-slate-700
            "
          >

            <Menu className="h-4 w-4" />

          </button>

        )}

      </div>



      {/* ======================================================
          NAVIGATION
          ====================================================== */}

      <nav
        className={`
          flex-1
          overflow-y-auto
          py-4
          ${collapsed ? 'px-2' : 'px-3'}
        `}
      >

        {!collapsed && (

          <div className="
            mb-2
            px-2
            text-[9px]
            font-bold
            uppercase
            tracking-[0.12em]
            text-slate-400
          ">
            Dashboard
          </div>

        )}


        <div className="flex flex-col gap-1">

          {navigationItems.map((item) => {

            const Icon = item.icon;

            const isActive =
              activeView === item.id;


            return (

              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.id)}
                title={collapsed ? item.label : undefined}
                className={`
                  group
                  relative
                  flex
                  h-[42px]
                  w-full
                  items-center
                  rounded-lg
                  transition-all
                  duration-150

                  ${collapsed
                    ? 'justify-center px-0'
                    : 'gap-3 px-3'
                  }

                  ${isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }
                `}
              >

                {/* Active indicator */}

                {isActive && (

                  <span
                    className="
                      absolute
                      left-0
                      top-1/2
                      h-6
                      w-[3px]
                      -translate-y-1/2
                      rounded-r-full
                      bg-blue-600
                    "
                  />

                )}


                {/* Icon */}

                <span
                  className={`
                    flex
                    h-7
                    w-7
                    shrink-0
                    items-center
                    justify-center
                    rounded-md

                    ${isActive
                      ? 'bg-blue-100 text-blue-600'
                      : 'text-slate-500 group-hover:text-slate-700'
                    }
                  `}
                >

                  <Icon className="h-[17px] w-[17px]" />

                </span>


                {/* Label */}

                {!collapsed && (

                  <span
                    className={`
                      truncate
                      text-[12px]
                      font-semibold
                      leading-4

                      ${isActive
                        ? 'text-blue-700'
                        : 'text-slate-600'
                      }
                    `}
                  >
                    {item.label}
                  </span>

                )}

              </button>

            );

          })}

        </div>

      </nav>



      {/* ======================================================
          SYSTEM STATUS
          ====================================================== */}

      <div
        className={`
          shrink-0
          border-t
          border-slate-100
          ${collapsed ? 'p-2' : 'p-3'}
        `}
      >

        <div
          className={`
            rounded-lg
            border
            border-emerald-100
            bg-emerald-50/70
            ${collapsed ? 'p-2' : 'p-3'}
          `}
        >

          <div
            className={`
              flex
              items-center
              ${collapsed
                ? 'justify-center'
                : 'gap-2'
              }
            `}
          >

            <span className="
              relative
              flex
              h-2
              w-2
              shrink-0
            ">

              <span className="
                absolute
                h-full
                w-full
                animate-ping
                rounded-full
                bg-emerald-400
                opacity-50
              />

              <span className="
                relative
                h-2
                w-2
                rounded-full
                bg-emerald-500
              />

            </span>


            {!collapsed && (

              <span className="
                text-[10px]
                font-bold
                leading-4
                text-emerald-700
              ">
                System Online
              </span>

            )}

          </div>


          {!collapsed && (

            <div className="
              mt-1
              flex
              items-center
              gap-1.5
              text-[9px]
              font-medium
              leading-3
              text-emerald-600
            ">

              <ShieldCheck className="h-3 w-3" />

              <span>
                All sensors operational
              </span>

            </div>

          )}

        </div>


        {!collapsed && (

          <div className="
            mt-3
            px-1
            text-center
            text-[8px]
            font-semibold
            uppercase
            leading-3
            tracking-[0.1em]
            text-slate-300
          ">
            REAL-TIME MONITORING
            <br />
            FOR SAFER FLIGHTS
          </div>

        )}

      </div>

    </aside>
  );
}