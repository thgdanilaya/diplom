select_all_orgs = """SELECT * FROM ProjectsDB.dbo.Procurement_Organization"""

insert_orgs = """INSERT INTO ProjectsDB.dbo.Procurement_Organization (ID_org) VALUES {0}"""

delete_orgs = """DELETE FROM ProjectsDB.dbo.Procurement_Organization WHERE ID_org IN {0}"""

select_null_names = """SELECT * FROM ProjectsDB.dbo.Procurement_Organization WHERE ID_org IS NOT NULL AND Name IS NULL"""

update_name = "UPDATE ProjectsDB.dbo.Procurement_Organization SET Name = '{0}' WHERE ID_org = {1}"

select_app_id = "SELECT ID,DateCreate,DateUpdate FROM ProjectsDB.dbo.Procurement WHERE ID = '{0}'"

insert_app = "INSERT INTO ProjectsDB.dbo.Procurement (ID, DateCreate, DateUpdate) VALUES ('{0}', '{1}', '{2}')"

update_app_mod_date = "UPDATE ProjectsDB.dbo.Procurement SET DateUpdate = '{0}' WHERE ID = '{1}'"