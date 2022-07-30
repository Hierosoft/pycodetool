# Notes on csharp-to-python

Manual changes are necessary after using Poikilos' (fork of
shannoncruey's) csharp-to-python.
The shim functions below were implemented manually in
<https://github.com/poikilos/RetractionTowerProcessor> and the latest versions of them can
be found there until they are implemented here.
- [ ] add them to fxshim.py


## String formatting overview
The dotnetfiddle.net output of
```CSharp
using System;

public class Program
{
    public static void Main()
    {
        decimal x = 0.1m;
        decimal y = 0.2m;
        decimal z = 0.32m;
        decimal retraction = 3m;
        Console.Write("z=\"");
        // Console.Write(z.ToString("#0.0000 ").PadLeft(8));
        Console.Write(z.ToString("##0.0").PadLeft(4));  // Having more #'s does nothing even though RetractionTestTowersGCodeGenerator does it :(
        // (# means only if present)
        Console.WriteLine("\"");
        Console.WriteLine("x=\""+"{0,5:##0.0}"+"\"", x);
        decimal a = 1.0m;
        Console.WriteLine("a=\"" + a.ToString("##0.#####") + "\"");
        decimal b = 1.123456m;
        Console.WriteLine("b=\"" + b.ToString("##0.#####") + "\"");
        decimal d = decimal.Parse("1");
        Console.WriteLine("d=\"" + d.ToString() + "\"");
    }
}
```
is
```
z=" 0.3"
x="  0.1"
a="1"
b="1.12346"
d="1"
```

## Issues

- convert enumerables
- convert iterators
  - See <https://treyhunner.com/2018/06/how-to-make-an-iterator-in-python/#Generator_functions>
  - `yield break` becomes `return` (Not `raise StopIteration`, which now creates a `RuntimeError` as of PEP 479)
- Classes within classes should be outside of classes.
- Bare calls to methods or access to members which are part of the class or object should specify `cls` (assuming `cls` is first param of `@classmethod`) or `self`
- C#-like names of imports (such as System) should be commented or removed
- `Math.Round(x)` should be "round(x)"
- `s.ToLowerInvariant()` and `s.ToLower(Char, CultureInfo.InvariantCulture)` should be `s.lower()`
- `l.Last()` should be `l[-1]`
- `s.PadLeft(4)` should be `s.rjust(4)` (Specifying the opposite side provides same chirality as original.)
- `s.PadRight(4)` should be `s.ljust(4)` (Specifying the opposite side provides same chirality as original.)
- `||` should be `or`
- `&&` should be `and`
- `if (command.Command == "G0") or (command.Command == "G1":` should be
  `if (command.Command == "G0") or (command.Command == "G1"):`
- `if command.HasParameter('Z':` should be
  `if command.HasParameter('Z'):`
- `char.IsDigit(s)` should be `s in "0123456789"`
- ```
string.IsNullOrWhiteSpace(s)
```
should be
```
def IsNullOrWhiteSpace(s):
    if s is None:
        return True
    if len(s) == 0:
        return True
    return str.isspace(s)
IsNullOrWhiteSpace(s)
- ```
stream.WriteLine(line)
```
should be
```
def StreamLine(stream, line):
    stream.write(line + "\n")
StreamLine(stream, line)
```
- ```
                line = reader.ReadLine()
                if line is None:
                    break
```
should be
```
            line = stream.readline()
            if not line:
                break
            line = line.rstrip()
```
- `Main(string[] args)` in program should be
```
    @classmethod
    def Main(cls, args):

```
  and the following is still necessary (args in C# doesn't include
      `argv[0]`):
      ```
if __name__ == "__main__":
    Program.Main(sys.argv[1:])

```
- `char.IsWhiteSpace(i, 1)` should be
  ```
def IsWhiteSpace(*args):
    '''
    Sequential arguments:
    1st (args[0]) -- String to check as a whole or as a character
    2nd (args[1]) -- If present, the second param is the index in
                     args[0] to check and no other parts of args[0] will
                     be checked.
    '''
    if len(args) == 1:
        return str.isspace(args[0])
    elif len(args) == 2:
        return str.isspace(args[0][args[1]])
    raise ValueError("IsWhiteSpace only takes (charStr)"
                     " or (str, index)")
IsWhiteSpace(i, 1)
```
- `true` should be `True`
- `false` should be `False`
- `z.ToString("#0.0")` should be `"{:.1f}".format(z)`
  (Always refactor when `ToString` has a param.)
- `(int)v` should be `int(v)`
- `curvePoints.Count(point => point.Z >= z)` should be `sum(1 for point in curvePoints if point.Z >= z)`
- generate a class instead of returning an anonymous class
  `static (Extent X, Extent Y, Extent Z) MeasureGCode(TextReader stream)`
  should be
  ```
    @staticmethod
    def MeasureGCode(stream):
        class AnonymousClass:
            pass
        result = AnonymousClass()
        result.X = Extent()
        result.Y = Extent()
        result.Z = Extent()
        return result
```
- Do not use Console:
  - `Console.Write(` should be `sys.stdout.write`
  - `Console.WriteLine(` should be `print(`
  - `Console.Error.Write(` should be `sys.stderr.write`
  - `Console.Error.WriteLine(s)` should be
```
def error(line):
    sys.stderr.write(line + "\n")
error(s)
```
  - `$"Retraction {retraction:0.00000} at Z {z:#0.0}"`
    (has `ValueError: Alternate form (#) not allowed in float format specifier`,
    `ValueError: Precision not allowed in integer format specifier`)
    should be
    `"Retraction {retraction:0.5f} at Z {z:.5f}".format(retraction=retraction, z=z)`
    (does show leading 0 for z < 1)
  - `print("Will write output to: {0}", outputFileName)` should be
    `print("Will write output to: {0}".format(outputFileName))`
- `decimal.Parse(` should be `float(`
- `Console.WriteLine(":X   {0,5:##0.0}    {1,5:##0.0}    {2,5:##0.0};", a, b, c)`
  should be
  `print("X   {0: >5.1f}    {1: >5.1f}    {2: >5.1f}".format(a, b, c))`
  - see `String.Format` for more details
- `String.Format` and `x.ToString(fmt)`:
  - The ## is meaningless (only shows the number if present) even though RetractionTestTowersGCodeGenerator uses it :(
  - Python behaviors:
    - `d`: decimal
    - `f`: fixed (fixed length)
    - `<` / `>`: align (left/right)
      - what precedes `>` is the padding character
      - what comes next is the number of spaces total to ensure for the length.
      - See string format documentation at
        <https://docs.python.org/3/library/string.html#formatspec>.
  - `n.ToString(##0.#####)`
    should be (requires fxshim.py to be copied to dest)
```
from fxshim import optionalD
optionalD(5).format(n)
# or:
# optionalD(5, mode="%") % n

```
- Remove operations in string interpolation:
```
$"=> Retract by {lastE - e} at Z {z}"
```
should be
```
'''
# should not be:
s = "=> Retract by {lastE - e} at Z {z}".format(
    lastE=lastE,
    z=z,
    e=e,
)
'''
# ^ C#-like operations in interpolations don't work
# should be:
s = "=> Retract by {0} at Z {z}".format(
    lastE - e,
    e=e,
)
```
- Constants ending with `m` or `M` (decimal specifier) should only need
  to end with `.0` if not already there before the letter.
- `List<T> l = new List<T>()` should be `l = []`
  - types before parameters should not be present at all
- `using (var reader = new StreamReader(fileName))`
  should be
  `with open(fileName, 'r') as reader:`
- `using (var writer = new StreamWriter(fileName))`
  should be
  `with open(fileName, 'w') as writer:`
- Streams should be disposed when they go out of scope.
  `extents = Program.MeasureGCode(Program.GetTemplateReader())`
  should be
  ```
        reader = Program.GetTemplateReader()
        try:
            extents = Program.MeasureGCode(reader)
        finally:
            reader.close()
```
  where `Program.GetTemplateReader` returns an open file.
- `Add` should be `append`
- `decimal.MinValue` should be `sys.float_info.min`
- `decimal.MaxValue` should be `sys.float_info.max`
- `some_generator(param).ToArray()` should be
  `list(some_generator(param))`
- `HashTable<T>` should become `set`
  - calls to its `Add` method should become `add`
  - calls to `set1.Count()` method should become `len(set1)`
-
```
    const decimal FirstTowerZ = 2.1m
```
should be
```
    FirstTowerZ = 2.1
```
or maybe (messy since all times it is accessed that would have to change to a call)
```
    _FirstTowerZ = 2.1
    @staticmethod
    def get_FirstTowerZ():
        return Program._FirstTowerZ

```
but NOT the following, since must be accessible without an instance
(a const is always static in C#)
```
'''
    @property
    def FirstTowerZ(self):
        return 2.1

    @FirstTowerZ.setter
    def FirstTowerZ(self, new_FirstTowerZ):
        '''
        Prevent changing FirstTowerZ in Python 3.
        '''
        # if new_price > 0 and isinstance(new_price, float):
        #     self._FirstTowerZ = new_FirstTowerZ
        raise RuntimeError("FirstTowerZ cannot be changed.")
'''
```

- The following additional changes are necessary:
```

                curvePoints.Add(
                    new CurvePoint()
                        PointType = CurvePointType.SameValueUntil,
                        Z = FirstTowerZ,
                        Retraction = 2m,
                    })
should be
                curvePoints.append(
                    CurvePoint(
                        PointType = CurvePointType.SameValueUntil,
                        Z = FirstTowerZ,
                        Retraction = 2.0,
                    )
                )
and the constructor must use kwargs to deal with this situation.

x.Length
should be
len(x)

stream.NewLine
should be
os.linesep

for (i = 0; i < len(command); i++)
should be
for i in range(len(command)):
HOWEVER: other languages tend to edit i, which doesn't stick in the next iteration in Python (so use while instead, but avoid issues with the `continue` statement)!

for (decimal z = 17.0m; z >= FirstTowerZ - GraphRowHeight; z -= GraphRowHeight)
should be
z = 17.0
while z >= FirstTowerZ - GraphRowHeight:
    . . .
    z -= GraphRowHeight
  - but avoid issues with the `continue` statement! For example, fix as:
i = -1
while i + 1 < 10:
    i += 1
    print(i)
- don't forget to specify the class name for static variables

Path.GetFullPath
should be
os.path.abspath

if (command.Command == "G0") or (command.Command == "G1":
should be
if (command.Command == "G0") or (command.Command == "G1"):

static TranslateGCode()
should be
@staticmethod
def TranslateGCode():

```

- `l.Sort((left, right) => left.Z.CompareTo(right.Z))` should be
  `l = sorted(l)`
  - However, sorting by lambda is totally unavailable in Python so you
    must override `__lt__` in the class from which elements of `l` are
    derived.
