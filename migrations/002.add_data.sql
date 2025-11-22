INSERT INTO departments (code, name) VALUES
    ('default', 'Default Department'),
    ('legal', 'Юридический отдел'),
    ('hr', 'Отдел кадров'),
    ('finance', 'Финансовый отдел'),
    ('it', 'IT-отдел'),
    ('security', 'Отдел безопасности'),
    ('accounting', 'Бухгалтерия'),
    ('marketing', 'Маркетинг'),
    ('sales', 'Отдел продаж'),
    ('qa', 'Отдел качества'),
    ('analytics', 'Аналитический отдел'),
    ('pr', 'PR-отдел'),
    ('rnd', 'Отдел исследований и разработок'),
    ('procurement', 'Отдел закупок'),
    ('support', 'Техническая поддержка')
ON CONFLICT (code) DO NOTHING;

INSERT INTO roles (code, name, description) VALUES
    ('admin',  'Administrator', 'Full administrative access'),
    ('moderator', 'Moderator',        'Can edit and approve documents'),
    ('viewer', 'Viewer',        'Can view documents and cases')
ON CONFLICT (code) DO NOTHING;


INSERT INTO permissions (code, description) VALUES
    ('documents.read',       'Read documents'),
    ('documents.write',      'Create and edit documents'),
    ('documents.approve',    'Approve document versions'),
    ('documents.delete',     'Delete documents'),

    ('cases.read',           'Read cases'),
    ('cases.write',          'Edit and answer cases'),
    ('cases.merge',          'Merge duplicated cases'),

    ('workspace.read',       'Read workspace items'),
    ('workspace.write',      'Edit workspace items'),

    ('admin.roles',          'Manage roles and permissions'),
    ('admin.users',          'Manage users')
ON CONFLICT (code) DO NOTHING;


INSERT INTO role_permissions (role_id, permission_code)
SELECT r.id, p.code
FROM roles r, permissions p
WHERE r.code = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_code)
SELECT r.id, p.code
FROM roles r
JOIN permissions p ON p.code IN (
    'documents.read',
    'documents.write',
    'documents.approve',
    'cases.read',
    'cases.write'
)
WHERE r.code = 'moderator'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_code)
SELECT r.id, p.code
FROM roles r
JOIN permissions p ON p.code IN (
    'documents.read',
    'cases.read'
)
WHERE r.code = 'viewer'
ON CONFLICT DO NOTHING;
