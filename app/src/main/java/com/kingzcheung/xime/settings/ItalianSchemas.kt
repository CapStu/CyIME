package com.kingzcheung.xime.settings

/**
 * 意大利语入口方案（assets/rime_italian/italian.schema.yaml）。它不组字：字母像英文一样逐字上屏，
 * 补全来自 [com.kingzcheung.xime.association.ItalianCompletion]。键盘是 xime.yaml 的 qwerty_italian。
 * 默认不启用：在「语言与方案」打开意大利语时才加入方案列表并部署。
 */
object ItalianSchemas {
    const val ID = "italian"
    val ids = listOf(ID)
}
