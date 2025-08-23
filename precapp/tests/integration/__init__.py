"""
Integration test package for comprehensive flow testing.

This package contains end-to-end integration tests that validate complete
business workflows across all modules in the precatorios system.

Test Organization:
- test_core_business_flows.py: Primary daily workflows
- test_administrative_flows.py: Administrative and configuration flows
- test_client_lifecycle_flows.py: Complete client management flows
- test_precatorio_lifecycle_flows.py: Complete precatorio management flows
- test_document_management_flows.py: Alvara & Requerimento workflows
- test_cross_module_integration.py: Multi-module integration scenarios
- test_error_handling_flows.py: Error scenarios and edge cases
- test_performance_flows.py: Performance and scalability scenarios
- test_security_flows.py: Security and permission flows

Each test module focuses on specific workflow categories while ensuring
complete coverage of all possible user journeys through the system.
"""
