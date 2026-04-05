//! Phenotype Macros Library
//!
//! Procedural macros for the Phenotype ecosystem including:
//! - Builder pattern derivation
//! - Error trait derivation  
//! - Contract trait derivation

use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

/// Derive the Builder pattern for a struct
/// 
/// # Example
/// ```
/// use phenotype_macros::Builder;
/// 
/// #[derive(Builder)]
/// struct MyStruct {
///     field: String,
/// }
/// ```
#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let builder_name = quote::format_ident!("{}Builder", name);
    
    // Extract struct fields
    let fields = match &input.data {
        syn::Data::Struct(data) => &data.fields,
        _ => panic!("Builder can only be derived for structs"),
    };
    
    // Generate builder fields (all Option<T>)
    let builder_fields = fields.iter().map(|f| {
        let name = &f.ident;
        let ty = &f.ty;
        quote! { #name: Option<#ty> }
    });
    
    // Generate builder methods
    let builder_methods = fields.iter().map(|f| {
        let name = &f.ident;
        let ty = &f.ty;
        quote! {
            pub fn #name(mut self, value: #ty) -> Self {
                self.#name = Some(value);
                self
            }
        }
    });
    
    // Generate field initializers
    let field_init = fields.iter().map(|f| {
        let name = &f.ident;
        quote! { #name: None }
    });
    
    // Generate build assignments
    let build_assign = fields.iter().map(|f| {
        let name = &f.ident;
        quote! { #name: self.#name? }
    });
    
    let expanded = quote! {
        impl #name {
            pub fn builder() -> #builder_name {
                #builder_name::new()
            }
        }
        
        pub struct #builder_name {
            #(#builder_fields,)*
        }
        
        impl #builder_name {
            pub fn new() -> Self {
                Self {
                    #(#field_init,)*
                }
            }
            
            #(#builder_methods)*
            
            pub fn build(self) -> Option<#name> {
                Some(#name {
                    #(#build_assign,)*
                })
            }
        }
    };
    
    TokenStream::from(expanded)
}

/// Derive the Contract trait for event/command types
#[proc_macro_derive(Contract)]
pub fn derive_contract(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    
    let expanded = quote! {
        impl Contract for #name {
            fn contract_type(&self) -> &'static str {
                stringify!(#name)
            }
            
            fn timestamp(&self) -> chrono::DateTime<chrono::Utc> {
                chrono::Utc::now()
            }
            
            fn correlation_id(&self) -> uuid::Uuid {
                uuid::Uuid::new_v4()
            }
        }
    };
    
    TokenStream::from(expanded)
}

/// Derive error trait implementations
#[proc_macro_derive(PhenotypeError)]
pub fn derive_error(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    
    let expanded = quote! {
        impl std::error::Error for #name {
            fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
                None
            }
        }
        
        impl std::fmt::Display for #name {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                write!(f, "{}", stringify!(#name))
            }
        }
    };
    
    TokenStream::from(expanded)
}
