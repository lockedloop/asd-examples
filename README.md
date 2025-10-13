# ASD setup

```
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

# Install ASD in editable mode
echo "Installing ASD in editable mode..."
pip install -e /Users/danilo/Git/asd # this is for dev only

# Verify installation
echo ""
echo "=== Verification ==="
echo "ASD location: $(which asd)"
echo "Python location: $(which python)"
echo ""

# Test asd command
echo "Testing ASD installation..."
asd --help > /dev/null && echo "✓ ASD command works!" || echo "✗ ASD command failed"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To activate the environment in the future, run:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo ""
echo "To initialize a test project:"
echo "  asd init --name my_test"
echo ""
echo "To deactivate the environment:"
echo "  deactivate"

```

