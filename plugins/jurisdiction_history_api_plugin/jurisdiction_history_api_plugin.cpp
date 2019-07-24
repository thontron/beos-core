#include <eosio/jurisdiction_history_api_plugin/jurisdiction_history_api_plugin.hpp>
#include <eosio/chain/exceptions.hpp>

#include <fc/io/json.hpp>

namespace eosio {

static appbase::abstract_plugin& _jurisdiction_history_api_plugin = app().register_plugin<jurisdiction_history_api_plugin>();

jurisdiction_history_api_plugin::jurisdiction_history_api_plugin(){}
jurisdiction_history_api_plugin::~jurisdiction_history_api_plugin(){}

void jurisdiction_history_api_plugin::set_program_options(options_description&, options_description&) {}

void jurisdiction_history_api_plugin::plugin_initialize(const variables_map&) 
{
   ilog( "initializing jurisdiction_history_api_plugin" );
}

#define CALL(api_name, api_handle, api_namespace, call_name, http_response_code) \
{std::string("/v1/" #api_name "/" #call_name), \
   [api_handle](string, string body, url_response_callback cb) mutable { \
          try { \
             if (body.empty()) body = "{}"; \
             auto result = api_handle.call_name(fc::json::from_string(body).as<api_namespace::call_name ## _params>()); \
             cb(http_response_code, fc::json::to_string(result)); \
          } catch (...) { \
             http_plugin::handle_exception(#api_name, #call_name, body, cb); \
          } \
       }}

#define CHAIN_RO_CALL(call_name, http_response_code) CALL(jurisdiction_history, ro_api, jurisdiction_history_apis::read_only, call_name, http_response_code)

void jurisdiction_history_api_plugin::plugin_startup()
{
   ilog( "starting jurisdiction_history_api_plugin" );

   auto ro_api = app().get_plugin<jurisdiction_history_plugin>().get_read_only_api();

   app().get_plugin<http_plugin>().add_api({
      CHAIN_RO_CALL(get_all_producer_jurisdiction_for_block, 200l),
      CHAIN_RO_CALL(get_producer_jurisdiction_for_block, 200l),
      CHAIN_RO_CALL(get_producer_jurisdiction_history, 200l)
   });
}

void jurisdiction_history_api_plugin::plugin_shutdown(){}

}