//! Phenotype Error Macros - Procedural macros for error handling
//!
//! Provides derive macros for error types with automatic ErrorCode,
//! Display, and From implementations.

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

use proc_macro::TokenStream;
use quote::{format_ident, quote};
use syn::{parse_macro_input, DeriveInput, Lit};

/// Derive macro for PhenotypeError trait
///
/// # Example
/// ```ignore
/// use phenotype_error_macros::PhenotypeError;
/// use phenotype_error_core::ErrorCode;
///
/// #[derive(Debug, PhenotypeError)]
/// #[error_code = "DOMAIN_ERROR"]
/// pub struct MyError {
///     message: String,
/// }
/// ```
#[proc_macro_derive(PhenotypeError, attributes(error_code, error_message))]
pub fn derive_phenotype_error(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let (impl_generics, ty_generics, where_clause) = input.generics.split_for_impl();

    // Parse error_code attribute
    let error_code = input
        .attrs
        .iter()
        .find_map(|attr| parse_string_attr(attr, "error_code"))
        .unwrap_or_else(|| "Unknown".to_string());

    // Parse error_message attribute
    let error_message = input
        .attrs
        .iter()
        .find_map(|attr| parse_string_attr(attr, "error_message"))
        .unwrap_or_else(|| format!("{} occurred", name));

    let error_code_variant = format_ident!("{}", error_code);

    let expanded = quote! {
        impl #impl_generics phenotype_error_core::PhenotypeError for #name #ty_generics #where_clause {
            fn code(&self) -> phenotype_error_core::ErrorCode {
                phenotype_error_core::ErrorCode::#error_code_variant
            }

            fn message(&self) -> String {
                #error_message.to_string()
            }
        }
    };

    TokenStream::from(expanded)
}

fn parse_string_attr(attr: &syn::Attribute, name: &str) -> Option<String> {
    if !attr.path().is_ident(name) {
        return None;
    }

    attr.parse_args::<Lit>().ok().and_then(|lit| {
        if let Lit::Str(s) = lit {
            Some(s.value())
        } else {
            None
        }
    })
}
