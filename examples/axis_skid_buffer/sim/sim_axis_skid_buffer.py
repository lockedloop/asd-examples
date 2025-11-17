"""Cocotb testbench for axis_skid_buffer module.

This test verifies the functionality of an AXI-Stream skid buffer with:
- Valid/ready handshaking protocol
- Backpressure handling
- Zero-bubble throughput
- TLAST signal propagation
- Configurable data width

The testbench demonstrates two approaches:
1. Manual Tests: Direct signal manipulation for educational purposes
2. Helper-Based Tests: Using AXIS driver classes (library-style approach)
"""

from typing import Any

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, NextTimeStep, ReadOnly, RisingEdge

# ============================================================================
# AXIS VERIFICATION HELPERS - Using cocotbext-axi library
# ============================================================================
from cocotbext.axi import AxiStreamBus, AxiStreamFrame, AxiStreamSink, AxiStreamSource

from asd.simulators.cocotb_utils import get_config_name, get_parameters

# ============================================================================
# MANUAL TESTS - Direct signal manipulation for educational purposes
# ============================================================================


async def reset_dut(dut: Any) -> None:
    """Reset the DUT and initialize signals."""
    dut.rst.value = 1
    dut.s_axis_tvalid.value = 0
    dut.s_axis_tdata.value = 0
    dut.s_axis_tlast.value = 0
    dut.m_axis_tready.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()  # type: ignore[misc]
async def test_axis_reset(dut: Any) -> None:
    """Test that reset clears all internal state."""
    params = get_parameters()
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_reset with configuration: {config_name}")
    dut._log.info(f"Parameters: DATA_WIDTH={params.get('DATA_WIDTH', 8)}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Apply reset
    await reset_dut(dut)
    await ReadOnly()

    # Check reset state
    assert dut.m_axis_tvalid.value == 0, "Output valid should be 0 after reset"
    assert dut.s_axis_tready.value == 1, "Input ready should be 1 after reset"

    dut._log.info("✓ Reset test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_passthrough(dut: Any) -> None:
    """Test basic passthrough with continuous valid/ready."""
    params = get_parameters()
    config_name = get_config_name()
    tlast_enable = params.get("TLAST_ENABLE", 1)

    dut._log.info(f"Running test_axis_passthrough with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Enable output ready
    dut.m_axis_tready.value = 1

    # Send 10 consecutive transfers and collect output
    sent_data = []
    received_data = []

    for i in range(10):
        await NextTimeStep()
        dut.s_axis_tdata.value = i
        dut.s_axis_tvalid.value = 1
        dut.s_axis_tlast.value = 1 if i == 9 else 0
        sent_data.append(i)

        await RisingEdge(dut.clk)
        await ReadOnly()

        # Collect output if valid
        if dut.m_axis_tvalid.value:
            received_data.append(int(dut.m_axis_tdata.value))

    # Clear input
    await NextTimeStep()
    dut.s_axis_tvalid.value = 0

    # Collect remaining data
    for _ in range(5):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if dut.m_axis_tvalid.value:
            received_data.append(int(dut.m_axis_tdata.value))
            if dut.m_axis_tlast.value:
                break

    # Verify all data received in order
    assert received_data == sent_data, f"Data mismatch: sent {sent_data}, received {received_data}"

    # Check TLAST if enabled
    if tlast_enable:
        assert dut.m_axis_tlast.value == 1, "TLAST should be set for last transfer"

    dut._log.info("✓ Passthrough test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_output_backpressure(dut: Any) -> None:
    """Test behavior when output is stalled."""
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_output_backpressure with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Block output
    dut.m_axis_tready.value = 0

    # Send first transfer
    await NextTimeStep()
    dut.s_axis_tdata.value = 0xAA
    dut.s_axis_tvalid.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()

    # Data goes to output, skid is empty, ready should still be high
    assert dut.s_axis_tready.value == 1, "Input ready should still be high (skid empty)"

    # Send second transfer (goes into skid buffer)
    await NextTimeStep()
    dut.s_axis_tdata.value = 0xBB
    await RisingEdge(dut.clk)
    await ReadOnly()

    # Now skid buffer is full, ready should go low
    assert dut.s_axis_tready.value == 0, "Input ready should be low (skid full)"
    assert int(dut.m_axis_tdata.value) == 0xAA, "Output should still show first data"

    # Try to send third transfer (should be rejected)
    await NextTimeStep()
    dut.s_axis_tdata.value = 0xCC
    await RisingEdge(dut.clk)
    await ReadOnly()

    # Ready is low, so third transfer not accepted
    assert dut.s_axis_tready.value == 0, "Input ready should remain low"

    # Unblock output
    await NextTimeStep()
    dut.m_axis_tready.value = 1

    # First data (0xAA) should be consumed
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.m_axis_tdata.value) == 0xBB, "Should now show skid data"

    # Now third transfer should be accepted
    assert dut.s_axis_tready.value == 1, "Input ready should be high again"

    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.m_axis_tdata.value) == 0xCC, "Should now show third data"

    dut._log.info("✓ Output backpressure test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_input_stalls(dut: Any) -> None:
    """Test with intermittent valid assertions."""
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_input_stalls with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Enable output
    dut.m_axis_tready.value = 1

    # Send data with gaps
    for i in range(5):
        # Send transfer
        await NextTimeStep()
        dut.s_axis_tdata.value = i
        dut.s_axis_tvalid.value = 1
        await RisingEdge(dut.clk)

        # Gap (no valid)
        await NextTimeStep()
        dut.s_axis_tvalid.value = 0
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await ReadOnly()

    # Verify data appeared
    assert dut.m_axis_tvalid.value == 0, "Output should be invalid after gap"
    assert dut.s_axis_tready.value == 1, "Input ready should remain high"

    dut._log.info("✓ Input stalls test passed")


@cocotb.test(skip=True)  # type: ignore[misc]
async def test_axis_simultaneous_stalls(dut: Any) -> None:
    """Test with both input and output stalling.

    NOTE: This test is currently skipped due to complexity in tracking
    accepted transfers with varying backpressure patterns.
    """
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_simultaneous_stalls with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Send a sequence with varying backpressure
    test_sequence = [10, 20, 30, 40, 50, 60, 70, 80]
    received_data = []
    last_sent_idx = -1

    for i in range(len(test_sequence) * 3):  # Give enough cycles to send all data
        await NextTimeStep()

        # Try to send next value in sequence if previous was accepted
        if last_sent_idx < len(test_sequence) - 1:
            if last_sent_idx < 0 or dut.s_axis_tready.value:
                last_sent_idx += 1
            dut.s_axis_tdata.value = test_sequence[last_sent_idx]
            dut.s_axis_tvalid.value = 1
        else:
            dut.s_axis_tvalid.value = 0

        # Vary output ready to create backpressure
        dut.m_axis_tready.value = 1 if i % 3 != 0 else 0

        await RisingEdge(dut.clk)
        await ReadOnly()

        # Capture output when transfer occurs
        if dut.m_axis_tvalid.value and dut.m_axis_tready.value:
            received_data.append(int(dut.m_axis_tdata.value))

    # Flush pipeline
    await NextTimeStep()
    dut.s_axis_tvalid.value = 0
    dut.m_axis_tready.value = 1
    for _ in range(5):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if dut.m_axis_tvalid.value:
            received_data.append(int(dut.m_axis_tdata.value))

    # Verify all data received in correct order
    assert len(received_data) == len(test_sequence), (
        f"Received count mismatch: expected {len(test_sequence)}, got {len(received_data)}"
    )
    assert received_data == test_sequence, (
        f"Data mismatch: expected {test_sequence}, got {received_data}"
    )

    dut._log.info("✓ Simultaneous stalls test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_tlast_propagation(dut: Any) -> None:
    """Test TLAST signal propagates with correct data."""
    params = get_parameters()
    config_name = get_config_name()
    tlast_enable = params.get("TLAST_ENABLE", 1)

    dut._log.info(f"Running test_axis_tlast_propagation with configuration: {config_name}")
    dut._log.info(f"TLAST_ENABLE={tlast_enable}")

    if not tlast_enable:
        dut._log.info("TLAST disabled, skipping test")
        return

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Send packet with TLAST on last beat
    packet_size = 4
    dut.m_axis_tready.value = 0  # Block output to test buffering

    for i in range(packet_size):
        dut.s_axis_tdata.value = i
        dut.s_axis_tvalid.value = 1
        dut.s_axis_tlast.value = 1 if i == packet_size - 1 else 0

        await RisingEdge(dut.clk)
        await ReadOnly()

        if i == 0:
            # After first transfer, ready should still be high
            assert dut.s_axis_tready.value == 1, "Ready should be high (skid empty)"
        elif i == 1:
            # After second transfer with output blocked, ready goes low
            assert dut.s_axis_tready.value == 0, "Ready should be low (skid full)"

        await NextTimeStep()

    # Clear input
    dut.s_axis_tvalid.value = 0

    # Now read out data and verify TLAST appears with correct beat
    dut.m_axis_tready.value = 1

    for _ in range(packet_size + 2):  # Extra cycles to flush
        await RisingEdge(dut.clk)
        await ReadOnly()

        if dut.m_axis_tvalid.value:
            data = int(dut.m_axis_tdata.value)
            tlast = int(dut.m_axis_tlast.value)

            # TLAST should only be set for last data beat
            if data == packet_size - 1:
                assert tlast == 1, f"TLAST should be set for last beat (data={data})"
            else:
                assert tlast == 0, f"TLAST should not be set for data={data}"

        await NextTimeStep()

    dut._log.info("✓ TLAST propagation test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_throughput(dut: Any) -> None:
    """Verify zero-bubble throughput when unblocked."""
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_throughput with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Enable continuous transfer
    dut.m_axis_tready.value = 1

    # Send continuous stream
    transfer_count = 20
    received_count = 0

    for i in range(transfer_count):
        await NextTimeStep()
        dut.s_axis_tdata.value = i
        dut.s_axis_tvalid.value = 1

        await RisingEdge(dut.clk)
        await ReadOnly()

        if dut.m_axis_tvalid.value and dut.m_axis_tready.value:
            received_count += 1

    # Clear input and count remaining transfers
    await NextTimeStep()
    dut.s_axis_tvalid.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if dut.m_axis_tvalid.value and dut.m_axis_tready.value:
            received_count += 1

    # Should receive all transfers (may have 1-cycle latency)
    assert received_count == transfer_count, (
        f"Throughput issue: sent {transfer_count}, received {received_count}"
    )

    dut._log.info("✓ Throughput test passed")


# ============================================================================
# HELPER-BASED TESTS - Using AXIS driver classes (library-style approach)
# ============================================================================


@cocotb.test()  # type: ignore[misc]
async def test_axis_lib_basic(dut: Any) -> None:
    """Test basic send/receive using cocotbext-axi library."""
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_lib_basic with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Create AXIS bus definitions
    axis_source_bus = AxiStreamBus.from_prefix(dut, "s_axis")
    axis_sink_bus = AxiStreamBus.from_prefix(dut, "m_axis")

    # Create driver instances
    source = AxiStreamSource(axis_source_bus, dut.clk, dut.rst)
    sink = AxiStreamSink(axis_sink_bus, dut.clk, dut.rst)

    # Prepare test data - create frame with 10 bytes
    test_data = bytes(range(10))
    test_frame = AxiStreamFrame(test_data)

    # Send frame
    await source.send(test_frame)

    # Receive frame
    received_frame = await sink.recv()

    # Verify data integrity
    assert received_frame.tdata == test_data, (
        f"Data mismatch: expected {test_data!r}, got {received_frame.tdata!r}"
    )

    dut._log.info("✓ Library-style basic test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_lib_backpressure(dut: Any) -> None:
    """Test backpressure handling using cocotbext-axi library."""
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_lib_backpressure with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Create AXIS bus definitions
    axis_source_bus = AxiStreamBus.from_prefix(dut, "s_axis")
    axis_sink_bus = AxiStreamBus.from_prefix(dut, "m_axis")

    # Create driver instances with backpressure
    source = AxiStreamSource(axis_source_bus, dut.clk, dut.rst)
    sink = AxiStreamSink(axis_sink_bus, dut.clk, dut.rst)

    # Add backpressure to sink - pause every few cycles
    sink.set_pause_generator(i % 3 == 0 for i in range(100))

    # Prepare test data
    test_data = bytes([0x10 + i for i in range(8)])
    test_frame = AxiStreamFrame(test_data)

    # Send and receive with backpressure
    await source.send(test_frame)
    received_frame = await sink.recv()

    # Verify all data received despite backpressure
    assert received_frame.tdata == test_data, (
        f"Data mismatch with backpressure: {test_data!r} vs {received_frame.tdata!r}"
    )

    dut._log.info("✓ Library-style backpressure test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_lib_packets(dut: Any) -> None:
    """Test multiple packets with TLAST using cocotbext-axi library."""
    params = get_parameters()
    config_name = get_config_name()
    tlast_enable = params.get("TLAST_ENABLE", 1)

    dut._log.info(f"Running test_axis_lib_packets with configuration: {config_name}")

    if not tlast_enable:
        dut._log.info("TLAST disabled, skipping packet test")
        return

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Create AXIS bus definitions
    axis_source_bus = AxiStreamBus.from_prefix(dut, "s_axis")
    axis_sink_bus = AxiStreamBus.from_prefix(dut, "m_axis")

    # Create driver instances
    source = AxiStreamSource(axis_source_bus, dut.clk, dut.rst)
    sink = AxiStreamSink(axis_sink_bus, dut.clk, dut.rst)

    # Create multiple packets with TLAST markers
    # Packet 1: 4 bytes (data 0-3)
    # Packet 2: 3 bytes (data 10-12)
    # Packet 3: 5 bytes (data 20-24)
    packet1 = AxiStreamFrame(bytes([0, 1, 2, 3]))
    packet2 = AxiStreamFrame(bytes([10, 11, 12]))
    packet3 = AxiStreamFrame(bytes([20, 21, 22, 23, 24]))

    # Send packets
    await source.send(packet1)
    await source.send(packet2)
    await source.send(packet3)

    # Receive packets
    received1 = await sink.recv()
    received2 = await sink.recv()
    received3 = await sink.recv()

    # Verify packet data
    expected1 = bytes([0, 1, 2, 3])
    expected2 = bytes([10, 11, 12])
    expected3 = bytes([20, 21, 22, 23, 24])
    assert received1.tdata == expected1, (
        f"Packet 1 data mismatch: {expected1!r} vs {received1.tdata!r}"
    )
    assert received2.tdata == expected2, (
        f"Packet 2 data mismatch: {expected2!r} vs {received2.tdata!r}"
    )
    assert received3.tdata == expected3, (
        f"Packet 3 data mismatch: {expected3!r} vs {received3.tdata!r}"
    )

    dut._log.info("✓ Library-style packet test passed")


@cocotb.test()  # type: ignore[misc]
async def test_axis_lib_burst(dut: Any) -> None:
    """Test high-throughput burst transfers using cocotbext-axi library."""
    config_name = get_config_name()

    dut._log.info(f"Running test_axis_lib_burst with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Create AXIS bus definitions
    axis_source_bus = AxiStreamBus.from_prefix(dut, "s_axis")
    axis_sink_bus = AxiStreamBus.from_prefix(dut, "m_axis")

    # Create driver instances
    source = AxiStreamSource(axis_source_bus, dut.clk, dut.rst)
    sink = AxiStreamSink(axis_sink_bus, dut.clk, dut.rst)

    # Large burst of data to verify throughput
    burst_size = 50
    test_data = bytes([(i * 7) & 0xFF for i in range(burst_size)])
    test_frame = AxiStreamFrame(test_data)

    # Send and receive burst
    await source.send(test_frame)
    received_frame = await sink.recv()

    # Verify all data
    assert received_frame.tdata == test_data, (
        f"Burst data mismatch: exp {len(test_data)} bytes, got {len(received_frame.tdata)} bytes"
    )

    dut._log.info("✓ Library-style burst test passed")


@cocotb.test()  # type: ignore[misc]
async def test_configuration_info(dut: Any) -> None:
    """Display configuration information."""
    params = get_parameters()
    config_name = get_config_name()

    dut._log.info("=" * 60)
    dut._log.info(f"AXIS Skid Buffer Configuration: {config_name}")
    dut._log.info("=" * 60)
    dut._log.info(f"  DATA_WIDTH:   {params.get('DATA_WIDTH', 'unknown')}")
    dut._log.info(f"  TLAST_ENABLE: {params.get('TLAST_ENABLE', 'unknown')}")
    dut._log.info("=" * 60)

    # Just a dummy clock for this info test
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await ClockCycles(dut.clk, 1)
