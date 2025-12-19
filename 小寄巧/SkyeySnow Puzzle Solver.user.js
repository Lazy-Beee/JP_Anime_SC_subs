// ==UserScript==
// @name         SkyeySnow Puzzle Solver
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  利用游戏原生逻辑自动拼图，保留最后一片供手动完成。
// @author       Gemini
// @match        https://www.skyey2.com//puzzle.php?img=*
// @grant        unsafeWindow
// ==/UserScript==

(function() {
    'use strict';

    // 创建操作按钮
    const btn = document.createElement('button');
    btn.innerText = "自动拼图 (留一片)";
    btn.style.cssText = "position: fixed; top: 10px; right: 10px; z-index: 99999; padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.3);";
    document.body.appendChild(btn);

    btn.onclick = function() {
        // 获取游戏核心对象 (兼容普通网页环境和Userscript沙箱环境)
        const win = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;
        const puzzle = win.mainPuzzle;

        if (!puzzle || !puzzle.piecesStart) {
            alert("游戏尚未加载完成，请稍后再试！");
            return;
        }

        // 定义安全计数器，防止死循环
        let safeGuard = puzzle.totalPieces + 10;

        // 循环直到只剩最后一片 (piecesInPlace < totalPieces - 1)
        while (puzzle.piecesInPlace < puzzle.totalPieces - 1 && safeGuard > 0) {
            safeGuard--;

            // 1. 获取当前待处理的碎片 (始终是 piecesStart) [cite: 190, 383]
            const p = puzzle.piecesStart;

            // 如果没有下一个碎片了(链表只剩一个)，为了防止报错停止逻辑（虽然上面的循环条件应该阻止了这种情况）
            if (!p || !p.next) break;

            // 2. 计算该碎片的正确目标位置
            // 逻辑源自 puzzle.js animate 函数 [cite: 193-194, 386-387]
            // 公式: (grid位置 * 大小) - (大小 * 0.2)
            const targetX = (p.gridX * p.size) - (p.size * 0.2);
            const targetY = (p.gridY * p.size) - (p.size * 0.2);

            // 3. 强制设置状态为“已归位”
            p.x = targetX;
            p.y = targetY;
            p.r = 0;           // 旋转角度归零 [cite: 196, 389]
            p.inPlace = true;  // 标记归位 [cite: 196, 389]

            // 4. 更新计数器
            puzzle.piecesInPlace++; // [cite: 196, 389]

            // 5. 链表操作：将当前碎片移到队尾，让下一个未拼的碎片变成 piecesStart
            // 逻辑源自 puzzle.js [cite: 197-198, 390-391]
            puzzle.piecesStart = p.next;
            puzzle.piecesStart.prev = null;

            p.prev = puzzle.piecesEnd;
            puzzle.piecesEnd.next = p;
            p.next = null;
            puzzle.piecesEnd = p;
        }

        // 6. 触发画面重绘
        // 设置全局标志位，让原生 animate 循环检测到变化并重绘 canvas [cite: 7, 200, 393]
        win.hasChanged = true;

        console.log(`自动完成进度: ${puzzle.piecesInPlace}/${puzzle.totalPieces}`);
    };
})();
