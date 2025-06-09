-- Test Supabase MCP by creating a sample table
CREATE TABLE IF NOT EXISTS test_mcp_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_data JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add some test data
INSERT INTO test_mcp_table (name, description, test_data) 
VALUES 
    ('Test Entry 1', 'First test entry for MCP', '{"status": "active", "priority": 1}'::jsonb),
    ('Test Entry 2', 'Second test entry for MCP', '{"status": "pending", "priority": 2}'::jsonb),
    ('Test Entry 3', 'Third test entry for MCP', '{"status": "completed", "priority": 3}'::jsonb);

-- Create an update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_test_mcp_table_updated_at BEFORE UPDATE
    ON test_mcp_table FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verify the table was created
SELECT * FROM test_mcp_table;