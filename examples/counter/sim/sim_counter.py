"""Cocotb testbench for counter module.

This test verifies the functionality of a parameterizable counter with:
- Synchronous reset
- Enable control
- Overflow detection
- Configurable width and maximum count
"""

from typing import Any

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, NextTimeStep, ReadOnly, RisingEdge

from asd.simulators.cocotb_utils import get_config_name, get_parameters


async def reset_dut(dut: Any) -> None:
    """Reset the DUT."""
    dut.rst.value = 1
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()  # type: ignore[misc]
async def test_counter_reset(dut: Any) -> None:
    """Test that reset clears counter and overflow."""
    # Get configuration
    params = get_parameters()
    config_name = get_config_name()

    dut._log.info(f"Running test_counter_reset with configuration: {config_name}")
    dut._log.info(f"Parameters: WIDTH={params.get('WIDTH', 8)}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Apply reset
    dut.rst.value = 1
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)

    # Check reset state
    assert dut.count.value == 0, f"Count should be 0 after reset, got {dut.count.value}"
    assert dut.overflow.value == 0, f"Overflow should be 0 after reset, got {dut.overflow.value}"

    dut._log.info("✓ Reset test passed")


@cocotb.test()  # type: ignore[misc]
async def test_counter_basic_counting(dut: Any) -> None:
    """Test basic counting functionality."""
    config_name = get_config_name()

    dut._log.info(f"Running test_counter_basic_counting with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Enable counter and count up
    dut.enable.value = 1

    for i in range(10):
        await RisingEdge(dut.clk)
        await ReadOnly()
        expected = i + 1
        actual = int(dut.count.value)
        assert actual == expected, f"Count mismatch at step {i}: expected {expected}, got {actual}"
        assert dut.overflow.value == 0, "Overflow should not be set during normal counting"

    dut._log.info("✓ Basic counting test passed")


@cocotb.test()  # type: ignore[misc]
async def test_counter_enable_control(dut: Any) -> None:
    """Test that counter holds value when enable is low."""
    config_name = get_config_name()

    dut._log.info(f"Running test_counter_enable_control with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Count to 5
    dut.enable.value = 1
    for _ in range(5):
        await RisingEdge(dut.clk)
        await ReadOnly()

    current_count = int(dut.count.value)
    assert current_count == 5, f"Count should be 5, got {current_count}"

    # Exit ReadOnly phase before writing
    await NextTimeStep()

    # Disable counter
    dut.enable.value = 0

    # Wait several cycles
    for _ in range(5):
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert int(dut.count.value) == current_count, (
            f"Count should hold at {current_count} when disabled"
        )

    dut._log.info("✓ Enable control test passed")


@cocotb.test()  # type: ignore[misc]
async def test_counter_overflow(dut: Any) -> None:
    """Test overflow behavior when counter reaches MAX_COUNT."""
    params = get_parameters()
    width = params.get("WIDTH", 8)
    max_count = (2**width) - 1  # Overflow triggers when all bits are 1
    config_name = get_config_name()

    dut._log.info(f"Running test_counter_overflow with configuration: {config_name}")
    dut._log.info(f"Testing overflow at WIDTH={width}, MAX_COUNT={max_count}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Enable counter
    dut.enable.value = 1

    # Count up to MAX_COUNT
    for i in range(max_count + 2):
        await RisingEdge(dut.clk)
        await ReadOnly()

        current_count = int(dut.count.value)
        overflow = int(dut.overflow.value)

        if i < max_count:
            # Before overflow
            assert overflow == 0, f"Overflow should be 0 before reaching MAX_COUNT (step {i})"
            assert current_count == i + 1, f"Count mismatch: expected {i + 1}, got {current_count}"
        elif i == max_count:
            # At overflow point
            assert overflow == 1, "Overflow should be set when reaching MAX_COUNT"
            assert current_count == 0, f"Count should wrap to 0 at overflow, got {current_count}"
        else:
            # After overflow
            assert overflow == 0, "Overflow should clear after wrapping"

    dut._log.info("✓ Overflow test passed")


@cocotb.test()  # type: ignore[misc]
async def test_counter_full_cycle(dut: Any) -> None:
    """Test a complete count cycle from 0 to MAX_COUNT and back."""
    params = get_parameters()
    config_name = get_config_name()
    width = params.get("WIDTH", 8)
    max_count = (2**width) - 1  # Overflow triggers when all bits are 1

    dut._log.info(f"Running test_counter_full_cycle with configuration: {config_name}")
    dut._log.info(f"Testing full cycle: WIDTH={width}, MAX_COUNT={max_count}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Enable counter
    dut.enable.value = 1

    # Count through entire range
    overflow_count = 0
    for i in range(max_count + 5):
        await RisingEdge(dut.clk)
        await ReadOnly()

        if int(dut.overflow.value) == 1:
            overflow_count += 1
            dut._log.info(
                f"Overflow detected at cycle {i}, count wrapped to {int(dut.count.value)}"
            )

    assert overflow_count >= 1, "Should have seen at least one overflow"
    dut._log.info(f"✓ Full cycle test passed (detected {overflow_count} overflows)")


@cocotb.test()  # type: ignore[misc]
async def test_counter_reset_during_count(dut: Any) -> None:
    """Test that reset works correctly during counting."""
    config_name = get_config_name()

    dut._log.info(f"Running test_counter_reset_during_count with configuration: {config_name}")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Count to some value
    dut.enable.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk)

    assert int(dut.count.value) > 0, "Count should be non-zero"

    # Reset again
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.count.value) == 0, "Count should be 0 after reset"
    assert int(dut.overflow.value) == 0, "Overflow should be 0 after reset"

    dut._log.info("✓ Reset during count test passed")


@cocotb.test()  # type: ignore[misc]
async def test_configuration_info(dut: Any) -> None:
    """Display configuration information."""

    params = get_parameters()
    config_name = get_config_name()

    dut._log.info("=" * 60)
    dut._log.info(f"Counter Configuration: {config_name}")
    dut._log.info("=" * 60)
    dut._log.info(f"  WIDTH:     {params.get('WIDTH', 'unknown')}")
    dut._log.info("=" * 60)

    # Just a dummy clock for this info test
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await ClockCycles(dut.clk, 1)
