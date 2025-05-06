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
          title: "License",
          description:"",
          icon: "key",
          href: "../settings/license",
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