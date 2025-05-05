import { Setting } from "../types/Setting"


export const SETTINGDATA : Setting[] = [
    {
      section: "Account",
      items: [
        {
          title: "My Account",
          description: "",
          icon: "person-circle-sharp",
          href: "../settings/profile", 
        },
        {
          title: "Licence",
          description:"",
          icon: "key",
          href: "../settings/license",
        },
      ],
    },
    {
      section: "Help",
      items: [
        {
          title: "FQA",
          description: "",
          icon: "help-circle-outline",
          href: "../settings/FQA",
        },
        {
          title: "About",
          description: "",
          icon: "information-circle-outline",
          href: "../settings/about",
        },
      ],
    },
    {
      section: "Actions",
      items: [
        {
          title: "Log Out",
          description: "",
          icon: "log-out-outline",
          action: "logout",
          logoutStyle: true,
        },
      ],
    },
  ];