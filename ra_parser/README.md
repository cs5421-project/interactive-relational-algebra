
## Literals
```
( letter | '_')( letter | digit | '_')*
```

## Grammar 
```
Query := Ident
Query := Query BinaryOp Query
Query := (Query)
Query := σ PYExprWithoutParenthesis (Query) | σ (PYExpr) (Query)
Query := π FieldList (Query)
Query := ρ RenameList (Query)
FieldList := Ident | Ident , FieldList
RenameList := Ident ➡ Ident | Ident ➡ Ident , RenameList
BinaryOp := * | - | ∪ | ∩ | ÷ | ⨝ | ⧑ | ⧒ | ⧓
```