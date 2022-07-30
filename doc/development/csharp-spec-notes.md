# C# Grammar spec notes

Multiple syntax groups may require a style of syntax, such as:
* "B.2.2 Types" and "B.2.7 Classes" both define type-parameter
* "B.2.5 Statements" and "B.2.7 Classes" both define constant-declarators
* "B.2.5 Statements" and "B.2.7 Classes" both define constant-declarator
* "B.2.2 Types" and "B.2.9 Arrays" both define rank-specifiers
* "B.2.2 Types" and "B.2.9 Arrays" both define rank-specifier
* "B.2.2 Types" and "B.2.9 Arrays" both define dim-separators
* and so on.

But duplication within a group doesn't appear intentional and should be ignored, such as:
- "B.2.7 Classes" defines member-name twice (same way)
