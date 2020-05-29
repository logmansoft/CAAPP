{
  "name"                 :  "Maintenance Project",
  "summary"              :  """It allows you to make maintenance project .""",
  "category"             :  "Maintenance",
  "version"              :  "1.0",
  "author"               :  "Slnee",
  "depends"              :  ['maintenance'],
  "data"                 :  [
                             'views/maintenance_project.xml',
                             'security/security.xml',
                             'security/ir.model.access.csv',
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False
}
