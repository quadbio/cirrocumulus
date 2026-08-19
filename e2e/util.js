const spawn = require('cross-spawn');
const path = require('node:path');
module.exports.diffImages = (image1, image2, tolerance) => {
  const result = spawn.sync(
    'gm',
    ['compare', '-metric', 'mse', path.resolve(image1), path.resolve(image2)],
    {encoding: 'utf-8'},
  );
  const output = result.stdout;
  if (result.error) {
    console.error('Failed to start process:', result.error);
    return false;
  }

  //            Normalized    Absolute
  //           ============  ==========
  //      Red: 0.0182117458     1193.5
  //    Green: 0.0152398829      998.7
  //     Blue: 0.0169042728     1107.8
  //    Total: 0.0167853005     1100.0
  const regex = /Total: (\d+\.?\d*)/m;
  const match = regex.exec(output);
  const equality = parseFloat(match[1]);
  return equality < tolerance;
};
