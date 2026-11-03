import React, { useState } from "react";
import {
  Maximize2,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  AlertTriangle,
  Box,
} from "lucide-react";

export default function Engine3DView() {
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);

  const zoomIn = () => {
    setZoom((value) => Math.min(value + 0.1, 1.5));
  };

  const zoomOut = () => {
    setZoom((value) => Math.max(value - 0.1, 0.7));
  };

  const rotate = () => {
    setRotation((value) => (value + 90) % 360);
  };

  const reset = () => {
    setZoom(1);
    setRotation(0);
  };

  return (
    <section className="w-full bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">

      {/* HEADER */}
      <header className="h-[68px] px-5 flex items-center justify-between border-b border-slate-100">

        <div className="flex items-center gap-3">

          <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center">
            <Box
              className="w-[18px] h-[18px] text-blue-600"
              strokeWidth={1.8}
            />
          </div>

          <div>
            <h2 className="text-[15px] leading-5 font-bold text-slate-900">
              2D Engine Inspection View
            </h2>

            <p className="text-[11px] leading-4 text-slate-500">
              Inspect the Rotax 914 engine image. Select a component for details.
            </p>
          </div>

        </div>

        <button
          type="button"
          title="Expand engine view"
          className="
            w-10 h-10
            rounded-lg
            border border-slate-200
            bg-white
            flex items-center justify-center
            text-slate-500
            hover:text-blue-600
            hover:border-blue-300
            hover:bg-blue-50
            transition
          "
        >
          <Maximize2
            className="w-[17px] h-[17px]"
            strokeWidth={1.8}
          />
        </button>

      </header>


      {/* ENGINE VIEW */}
      <div className="px-4 pt-3">

        <div
          className="
            relative
            w-full
            h-[285px]
            rounded-lg
            overflow-hidden
            border border-slate-200
            bg-[#071a26]
          "
        >

          {/* 2D MODEL LABEL */}
          <div className="absolute top-3 left-3 z-30">

            <div
              className="
                flex items-center gap-2
                px-3 py-2
                bg-white
                rounded-md
                border border-slate-200
                shadow-sm
              "
            >

              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />

              <span className="text-[10px] font-bold tracking-wide text-slate-600">
                2D MODEL
              </span>

            </div>

          </div>


          {/* ZOOM INDICATOR */}
          <div className="absolute top-3 right-3 z-30">

            <div
              className="
                min-w-[60px]
                h-9
                px-3
                flex items-center justify-center
                bg-white
                rounded-md
                border border-slate-200
                shadow-sm
              "
            >

              <span className="text-[10px] font-mono font-bold text-slate-500">
                {zoom.toFixed(2)}x
              </span>

            </div>

          </div>


          {/* ENGINE IMAGE */}
          <div className="absolute inset-0 flex items-center justify-center overflow-hidden">

            <img
              src="/engine_3d.png"
              alt="Rotax 914 engine"
              draggable="false"
              className="
                block
                select-none
                pointer-events-none
                w-full
                h-full
                object-contain
                transition-transform
                duration-300
                ease-out
              "
              style={{
                transform: `scale(${zoom}) rotate(${rotation}deg)`,
                transformOrigin: "center center",
              }}
            />

          </div>


          {/* CYLINDER 3 MARKER */}
          <div
            className="
              absolute
              left-[54%]
              top-[43%]
              z-20
            "
          >

            <div className="relative">

              <div
                className="
                  absolute
                  -left-[7px]
                  -top-[7px]
                  w-[26px]
                  h-[26px]
                  rounded-full
                  bg-red-500/20
                  animate-pulse
                "
              />

              <div
                className="
                  relative
                  w-[13px]
                  h-[13px]
                  rounded-full
                  bg-red-500
                  border-2
                  border-white
                  shadow-lg
                "
              />

              <div
                className="
                  absolute
                  left-5
                  top-[-17px]
                  whitespace-nowrap
                  bg-white
                  border
                  border-red-200
                  rounded-lg
                  shadow-md
                  px-3
                  py-2
                  min-w-[100px]
                "
              >

                <div className="flex items-center gap-2">

                  <span className="w-2 h-2 rounded-full bg-red-500" />

                  <span className="text-[10px] font-bold text-slate-800">
                    Cylinder 3
                  </span>

                </div>

                <div className="text-[9px] font-bold text-red-600 mt-1">
                  CHT: 185 °C
                </div>

              </div>

            </div>

          </div>


          {/* ALERT */}
          <div className="absolute bottom-3 left-3 z-30">

            <div
              className="
                flex items-center gap-2
                px-3 py-2
                bg-white
                border border-amber-300
                rounded-lg
                shadow-sm
              "
            >

              <AlertTriangle
                className="w-[15px] h-[15px] text-amber-500 shrink-0"
                strokeWidth={1.8}
              />

              <span className="text-[10px] font-semibold text-amber-700 whitespace-nowrap">
                Alert: Cylinder 3 CHT running +25°C higher than nominal baseline.
              </span>

            </div>

          </div>

        </div>

      </div>


      {/* CONTROLS */}
      <div className="flex justify-center py-3">

        <div
          className="
            inline-flex
            items-center
            bg-white
            border border-slate-200
            rounded-full
            shadow-md
            px-2
            h-[46px]
          "
        >

          {/* ROTATE */}
          <button
            type="button"
            onClick={rotate}
            className="
              h-8
              px-4
              flex
              items-center
              gap-2
              rounded-full
              text-[10px]
              font-bold
              text-blue-600
              hover:bg-blue-50
              transition
            "
          >

            <RotateCcw
              className="w-[15px] h-[15px]"
              strokeWidth={1.8}
            />

            <span>Rotate</span>

          </button>


          <div className="w-px h-5 bg-slate-200" />


          {/* ZOOM OUT */}
          <button
            type="button"
            onClick={zoomOut}
            title="Zoom out"
            className="
              w-9
              h-8
              flex
              items-center
              justify-center
              rounded-full
              text-slate-500
              hover:text-blue-600
              hover:bg-blue-50
              transition
            "
          >

            <ZoomOut
              className="w-[15px] h-[15px]"
              strokeWidth={1.8}
            />

          </button>


          <span
            className="
              px-2
              text-[10px]
              font-medium
              text-slate-500
              min-w-[40px]
              text-center
            "
          >
            Zoom
          </span>


          {/* ZOOM IN */}
          <button
            type="button"
            onClick={zoomIn}
            title="Zoom in"
            className="
              w-9
              h-8
              flex
              items-center
              justify-center
              rounded-full
              text-slate-500
              hover:text-blue-600
              hover:bg-blue-50
              transition
            "
          >

            <ZoomIn
              className="w-[15px] h-[15px]"
              strokeWidth={1.8}
            />

          </button>


          <div className="w-px h-5 bg-slate-200" />


          {/* RESET */}
          <button
            type="button"
            onClick={reset}
            title="Reset view"
            className="
              h-8
              px-4
              flex
              items-center
              gap-2
              rounded-full
              text-[10px]
              font-bold
              text-slate-600
              hover:bg-slate-50
              transition
            "
          >

            <RotateCcw
              className="w-[15px] h-[15px]"
              strokeWidth={1.8}
            />

            <span>Reset</span>

          </button>

        </div>

      </div>

    </section>
  );
}