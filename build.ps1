$OUTPUT_DIR="output"
$ARCHITECTURE="x64"
$GENERATOR="Visual Studio 17 2022"
$CONFIG="Release"

python -m pip install -r requirements.txt

conan profile detect --force

Remove-Item -ea Ignore -Force -r $OUTPUT_DIR
mkdir $OUTPUT_DIR
Set-Location $OUTPUT_DIR

cmake .. -A $ARCHITECTURE -G $GENERATOR
cmake --build . --config $CONFIG -- /verbosity:detailed
Set-Location ..