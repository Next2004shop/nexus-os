/**
 * NEXUS Native Engine — pybind11 Python Bindings
 * ================================================
 * Phase CPP-2: Exposes the C++ engine to Python via pybind11.
 *
 * Module name: nexus_native_ext
 *   (underscore-prefixed from the Python bridge's perspective;
 *    the public Python API is native_engine/python_bridge/nexus_native.py)
 *
 * Exposed symbols:
 *   Classes:   MarketData, TickData, SignalResult, RiskResult, TickResult
 *   Functions: compute_signal(), compute_risk(), process_tick()
 *   Helpers:   engine_version(), is_native_available()
 *
 * Design notes:
 *   - All struct fields are exposed as read-write Python attributes.
 *   - to_dict() methods on result types allow idiomatic Python usage.
 *   - No numpy dependency in bindings — plain Python dicts are used.
 *     CPP-3 will add numpy buffer-protocol bindings for array inputs.
 *   - pybind11/stl.h provides automatic std::string ↔ str conversion.
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "engine.hpp"
#include "indicators.hpp"
#include "risk.hpp"

namespace py = pybind11;
using namespace nexus;

PYBIND11_MODULE(nexus_native_ext, m) {

    m.doc()             = "NEXUS Native Engine — C++ acceleration layer "
                          "for high-frequency trading computations";
    m.attr("__version__") = "0.1.0-alpha";
    m.attr("__phase__")   = "CPP-2";

    // =======================================================
    // MarketData
    // =======================================================
    py::class_<MarketData>(m, "MarketData",
        "Normalized OHLCV bar. Feed with data from Polygon.io REST or "
        "the MT5 bridge before calling compute_signal().")

        .def(py::init<>())
        .def(py::init<const std::string&,
                      double, double, double, double,
                      double, int64_t>(),
             py::arg("symbol"),
             py::arg("open"),  py::arg("high"),
             py::arg("low"),   py::arg("close"),
             py::arg("volume"), py::arg("timestamp_ms"))

        .def_readwrite("symbol",       &MarketData::symbol)
        .def_readwrite("open",         &MarketData::open)
        .def_readwrite("high",         &MarketData::high)
        .def_readwrite("low",          &MarketData::low)
        .def_readwrite("close",        &MarketData::close)
        .def_readwrite("volume",       &MarketData::volume)
        .def_readwrite("timestamp_ms", &MarketData::timestamp_ms)

        .def("__repr__", [](const MarketData& d) {
            return "<MarketData symbol='" + d.symbol
                 + "' close=" + std::to_string(d.close) + ">";
        });


    // =======================================================
    // TickData
    // =======================================================
    py::class_<TickData>(m, "TickData",
        "Real-time bid/ask tick. Populate from LiveDataManager.ticks{} "
        "before calling process_tick().")

        .def(py::init<>())
        .def_readwrite("symbol",       &TickData::symbol)
        .def_readwrite("bid",          &TickData::bid)
        .def_readwrite("ask",          &TickData::ask)
        .def_readwrite("last",         &TickData::last)
        .def_readwrite("volume",       &TickData::volume)
        .def_readwrite("timestamp_ms", &TickData::timestamp_ms)

        .def("spread", &TickData::spread,
             "Raw spread: ask - bid (not pip-normalised)")
        .def("mid", &TickData::mid,
             "Mid-price: (bid + ask) / 2")

        .def("__repr__", [](const TickData& t) {
            return "<TickData symbol='" + t.symbol
                 + "' bid=" + std::to_string(t.bid)
                 + " ask=" + std::to_string(t.ask) + ">";
        });


    // =======================================================
    // SignalResult
    // =======================================================
    py::class_<SignalResult>(m, "SignalResult",
        "Output of compute_signal(). "
        "direction: +1=BUY, 0=NEUTRAL, -1=SELL.")

        .def(py::init<>())
        .def_readwrite("direction",  &SignalResult::direction)
        .def_readwrite("confidence", &SignalResult::confidence)
        .def_readwrite("score",      &SignalResult::score)
        .def_readwrite("reason",     &SignalResult::reason)
        .def_readwrite("valid",      &SignalResult::valid)

        .def("direction_str", [](const SignalResult& r) -> std::string {
            return r.direction_str();
        }, "Human-readable direction: 'BUY', 'SELL', or 'NEUTRAL'")

        .def("to_dict", [](const SignalResult& r) {
            py::dict d;
            d["direction"]     = r.direction;
            d["direction_str"] = std::string(r.direction_str());
            d["confidence"]    = r.confidence;
            d["score"]         = r.score;
            d["reason"]        = r.reason;
            d["valid"]         = r.valid;
            return d;
        }, "Return result as a Python dict (compatible with existing Python pipeline)")

        .def("__repr__", [](const SignalResult& r) {
            return std::string("<SignalResult direction=")
                 + r.direction_str()
                 + " confidence=" + std::to_string(r.confidence) + ">";
        });


    // =======================================================
    // RiskResult
    // =======================================================
    py::class_<RiskResult>(m, "RiskResult",
        "Output of compute_risk(). "
        "allowed=False in CPP-2; full logic in CPP-3.")

        .def(py::init<>())
        .def_readwrite("allowed",       &RiskResult::allowed)
        .def_readwrite("position_size", &RiskResult::position_size)
        .def_readwrite("stop_loss",     &RiskResult::stop_loss)
        .def_readwrite("take_profit",   &RiskResult::take_profit)
        .def_readwrite("risk_reward",   &RiskResult::risk_reward)
        .def_readwrite("reason",        &RiskResult::reason)

        .def("to_dict", [](const RiskResult& r) {
            py::dict d;
            d["allowed"]       = r.allowed;
            d["position_size"] = r.position_size;
            d["stop_loss"]     = r.stop_loss;
            d["take_profit"]   = r.take_profit;
            d["risk_reward"]   = r.risk_reward;
            d["reason"]        = r.reason;
            return d;
        }, "Return result as a Python dict")

        .def("__repr__", [](const RiskResult& r) {
            return std::string("<RiskResult allowed=")
                 + (r.allowed ? "True" : "False")
                 + " size=" + std::to_string(r.position_size) + ">";
        });


    // =======================================================
    // TickResult
    // =======================================================
    py::class_<TickResult>(m, "TickResult",
        "Output of process_tick(). "
        "processing_latency_us is wall-clock time inside C++.")

        .def(py::init<>())
        .def_readwrite("symbol",                &TickResult::symbol)
        .def_readwrite("processed_price",       &TickResult::processed_price)
        .def_readwrite("spread_pips",           &TickResult::spread_pips)
        .def_readwrite("is_stale",              &TickResult::is_stale)
        .def_readwrite("processing_latency_us", &TickResult::processing_latency_us)

        .def("to_dict", [](const TickResult& r) {
            py::dict d;
            d["symbol"]                = r.symbol;
            d["processed_price"]       = r.processed_price;
            d["spread_pips"]           = r.spread_pips;
            d["is_stale"]              = r.is_stale;
            d["processing_latency_us"] = r.processing_latency_us;
            return d;
        }, "Return result as a Python dict");


    // =======================================================
    // NexusEngine class
    // =======================================================
    py::class_<NexusEngine>(m, "NexusEngine",
        "Primary C++ computation engine. "
        "Prefer module-level free functions for simplicity. "
        "Use this class directly to maintain per-instance state.")

        .def(py::init<>())
        .def("compute_signal", &NexusEngine::compute_signal,
             py::arg("data"),
             "Compute trading signal from a MarketData bar")
        .def("compute_risk",   &NexusEngine::compute_risk,
             py::arg("symbol"), py::arg("side"),
             py::arg("entry_price"), py::arg("account_balance"),
             py::arg("risk_pct") = 0.01,
             "Evaluate risk parameters for a proposed trade")
        .def("process_tick",   &NexusEngine::process_tick,
             py::arg("tick"),
             "Process an incoming market tick")
        .def("version",        &NexusEngine::version,
             "Library version string")
        .def("is_ready",       &NexusEngine::is_ready,
             "True once constructor completes");


    // =======================================================
    // Module-level free functions
    // =======================================================
    m.def("compute_signal", &nexus::compute_signal,
          py::arg("data"),
          "Compute trading signal from a MarketData bar (uses global engine)");

    m.def("compute_risk",   &nexus::compute_risk,
          py::arg("symbol"), py::arg("side"),
          py::arg("entry_price"), py::arg("account_balance"),
          py::arg("risk_pct") = 0.01,
          "Evaluate risk parameters for a proposed trade (uses global engine)");

    m.def("process_tick",   &nexus::process_tick,
          py::arg("tick"),
          "Process an incoming market tick (uses global engine)");


    // =======================================================
    // Utility / health
    // =======================================================
    m.def("engine_version", []() -> std::string {
        return "0.1.0-alpha";
    }, "Return native engine version string");

    m.def("is_native_available", []() -> bool {
        return true;
    }, "Always True when this compiled extension is loaded");

    m.def("engine_phase", []() -> std::string {
        return "CPP-2";
    }, "Return current development phase of the native engine");

} // PYBIND11_MODULE
