# Barrister namespace proposal

## Goals

* Allow IDL file to import other IDL files to scope in structs/enums
* Expose namespace information for structs/enums via IDL JSON
* Allow code generation tools (e.g. idl2java) access to entity/enum namespaces

## Non-Goals

* Exporting interfaces from IDL files.  Interfaces are not designed to be re-used or inherited, so exporting them is not useful.

## Implementation notes

* Translation from `.idl` to `.json` still starts from a single root `.idl` file.  This is unchanged.
* IDL parsing is two-pass
  * Recursive IDL file loading - Staring with the root IDL file, each file is parsed for `import` statements
    * Each unique file (based on MD5 hash of the file contents) is in turn scanned for more imports
    * This repeats until all unique import statements have been run and all IDL file contents parsed
    * If any referenced import file cannot be found, the parser terminates with an error
  * IDL validation
    * All referenced user defined types are checked to ensure that their fields are present
    * Struct cycles are detected
    * Duplicate types are detected
* A single `.json` file is still emitted per execution.  Any imported types that are reachable from the root IDL file are
  included in the JSON file.
  * The `import` mechanism is purely a translation time concern and is equivalent to copy and pasting the contents into the
    root IDL file with the namespace (if any) prefixed

## Example

`common.idl`

    namespace common

    struct PaginatedResult {
    	totalRows      int
    	startOffset    int
    }

    enum SortDir {
        ASC
        DESC
    }

    struct SortBy {
        name           string
        direction      SortDir
    }

    struct Pagination {
    	startOffset    int
    	maxRows        int
    }

    struct Locale {
        language  string
        country   string
    }

`project.idl`

    namespace project

    // barrister parser would look for: "common.idl" in same dir as project.idl
    // it would also be useful to have a BARRISTER_PATH env var that could provide
    // directories to traverse.  
    import "common.idl"

    // might also be useful to allow paths -- path separator would need to be sanitized
    // to OS separator, but could be canonically defined as forward slashes
    // import "../common.idl"

    // use imported struct
    struct ProjectPaginatedResult extends common.PaginatedResult {
        rows       []Project
    }

    struct Project {
    	name    string
    }

    interface ProjectService {
    	// use exported SortBy and Pagination structs as params
    	searchByName(name string, sort common.SortBy, pagination common.Pagination) ProjectPaginatedResult
    }

When we run barrister against: `project.idl` we get this `project.json`

    [{
	    "comment": "",
	    "extends": "",
	    "type": "struct",
	    "name": "common.PaginatedResult",
	    "fields": [{
	        "comment": "",
	        "optional": false,
	        "is_array": false,
	        "type": "int",
	        "name": "totalRows"
	    }, {
	        "comment": "",
	        "optional": false,
	        "is_array": false,
	        "type": "int",
	        "name": "startOffset"
	    }]
	}, {
	    "comment": "",
	    "values": [{
	        "comment": "",
	        "value": "ASC"
	    }, {
	        "comment": "",
	        "value": "DESC"
	    }],
	    "type": "enum",
	    "name": "common.SortDir"
	}, {
	    "comment": "",
	    "extends": "",
	    "type": "struct",
	    "name": "common.SortBy",
	    "fields": [{
	        "comment": "",
	        "optional": false,
	        "is_array": false,
	        "type": "string",
	        "name": "name"
	    }, {
	        "comment": "",
	        "optional": false,
	        "is_array": false,
	        "type": "common.SortDir",
	        "name": "direction"
	    }]
	}, {
	    "comment": "",
	    "extends": "",
	    "type": "struct",
	    "name": "common.Pagination",
	    "fields": [{
	        "comment": "",
	        "optional": false,
	        "is_array": false,
	        "type": "int",
	        "name": "startOffset"
	    }, {
	        "comment": "",
	        "optional": false,
	        "is_array": false,
	        "type": "int",
	        "name": "maxRows"
	    }]
	}, {
	    "comment": "",
	    "extends": "common.PaginatedResult",
	    "type": "struct",
	    "name": "project.ProjectPaginatedResult",
	    "fields": [{
	        "comment": "",
	        "optional": false,
	        "is_array": true,
	        "type": "project.Project",
	        "name": "rows"
	    }]
	}, {
	    "comment": "",
	    "extends": "",
	    "type": "struct",
	    "name": "project.Project",
	    "fields": [{
	        "comment": "",
	        "optional": false,
	        "is_array": false,
	        "type": "string",
	        "name": "name"
	    }]
	}, {
	    "comment": "",
	    "functions": [{
	        "comment": "use exported SortBy and Pagination structs as params",
	        "returns": {
	            "optional": false,
	            "is_array": false,
	            "type": "project.ProjectPaginatedResult"
	        },
	        "params": [{
	            "is_array": false,
	            "type": "string",
	            "name": "name"
	        }, {
	            "is_array": false,
	            "type": "SortBy",
	            "name": "sort"
	        }, {
	            "is_array": false,
	            "type": "common.Pagination",
	            "name": "pagination"
	        }],
	        "name": "searchByName"
	    }],
	    "type": "interface",
	    "name": "project.ProjectService"
	}, {
	    "barrister_version": "0.1.4",
	    "type": "meta",
	    "date_generated": 1362938499297,
	    "checksum": "5ded270c3c64ab55d1a2505a37dadebb"
	}]

## Re-using namespace in multiple IDL files

While perhaps inadvisable, the same namespace may be used in multiple IDL files.  This keeps the implementation simple, as 
there's no hard relationship between a namespace and a filename.

For example:

`a.idl`

	namespace project

	struct Project {
		name  string
	}

`b.idl`

	namespace project

	enum ProjectType {
		USER
		SYSTEM
	}

## Nested import

It should be possible to nest imports.  For example, this should be valid

`food.idl`

	namespace food

	struct Ingredient {
		name  string
	}

`menu.idl`

	namespace menu

	import "food.idl"

    struct Dish {
    	name         string
        ingredients  []food.Ingredient
    }

	struct Menu {
		dishes []Dish
	}

`restaurant.idl`

    import "menu.idl"

    interface Restaurant {

        getMenu() menu.Menu
        getDishesByIngredient(ingredientName string) []menu.Dish

    }

Imports are not automatically transitive.  For example, the following is *invalid* 

`invalid-restaurant.idl`

    import "menu.idl"

    interface Restaurant {

        // Invalid:  'food' namespace is not in scope
        getIngredientsForDish(dishName string) food.Ingredient

        getMenu() menu.Menu

    }

To fix this, "food.idl" must be imported directly.

`ok-restaurant.idl`

    import "menu.idl"
    import "food.idl"

    interface Restaurant {

        getIngredientsForDish(dishName string) food.Ingredient
        getMenu() menu.Menu

    }

## Import order should not matter

`import` statements within a file should produce a valid scope anywhere within the same file.

For example, the above `ok-restaurant.idl` could be rewritten this way, with equivalent behavior:

    interface Restaurant {

        getIngredientsForDish(dishName string) food.Ingredient
        getMenu() menu.Menu

    }

    import "food.idl"
    import "menu.idl"

## Circular imports

While inadvisable, circular imports will be permitted.  The MD5 checksum of the file contents will be used
to determine whether a given file has been loaded before.  For example:

`a.idl`

    namespace a

    import "b.idl"

    struct A {
        name string
        type b.Type
    }

    enum Color {
        red
        blue
    }

`b.idl`

    namespace b

    import "a.idl"

    struct B {
    	name   string
    	color  a.Color
    	type   Type
    }

    enum Type {
    	good
    	bad
    }

Note that circular type references are still prohibited.

`invalid-a.idl`

    namespace a

    import "b.idl"

    struct A {
        name string
        myB  b.B
    }

`invalid-b.idl`

    namespace b

    import "a.idl"

    // creates a cycle - prohibited
    struct B {
    	name   string
    	myA    a.A
    }

## Invalid: Name collision

If two or more IDL files in the current parse tree declare a type with the same name within the same namespace,
the parser should raise an error.  This is similar to the current (non-namespace) behavior.

For example:

`a-1.idl`

    namespace a

    struct Foo {
    	name string
    }

`a-2.idl`

    namespace a

    struct Foo {
        age   int
    }

`invalid-service.idl`

    import "a-1.idl"
    import "a-2.idl"

    interface FooService {
    	saveFoo(foo Foo) int
    }

However, this *will* work because the parser won't know about `a-1.idl`

`ok-service.idl`

    // only importing one of the 'a' files
    import "a-2.idl"

    interface FooService {
    	saveFoo(foo Foo) int
    }


